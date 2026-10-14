<?php
/**
 * CMS entry point / router.
 *
 * GET  ?page=<view>   renders a view (login gate applied)
 * POST ?do=<action>   runs actions/<action>.php (whitelisted)
 *
 * Run locally with the site root as docroot so ../dist works relatively:
 *   cd ~/workspace/shaheen-website && php -S localhost:8000
 * then open http://localhost:8000/admin/
 * Under XAMPP place the site folder in htdocs and open /<site>/admin/.
 */
declare(strict_types=1);

require __DIR__ . '/inc/helpers.php';
require __DIR__ . '/inc/db.php';
require __DIR__ . '/inc/csrf.php';
require __DIR__ . '/inc/auth.php';
require __DIR__ . '/inc/content.php';

session_boot();

/* ------------------------------------------------ action dispatch (POST) */
$do = $_POST['do'] ?? $_GET['do'] ?? null;
if ($_SERVER['REQUEST_METHOD'] === 'POST' && $do !== null) {
    csrf_require();
    $do = (string)$do;
    // Whitelist: file must exist in actions/.
    if (!preg_match('#^[a-z0-9_]+$#', $do) || !is_file(__DIR__ . '/actions/' . $do . '.php')) {
        http_response_code(400);
        die('Unknown action.');
    }
    require __DIR__ . '/actions/' . $do . '.php';
    exit; // actions must redirect or die; this is a safety net.
}

/* ------------------------------------------------ first-run setup */
$noUsers = false;
try { $noUsers = user_count() === 0; } catch (Throwable $t) { /* db errors surface on setup page */ }

$page = $_GET['page'] ?? 'dashboard';
if (!preg_match('#^[a-z0-9_]+$#', (string)$page)) $page = 'dashboard';

if ($noUsers && $page !== 'setup') {
    redirect(admin_url('setup'));
}

/* ------------------------------------------------ public pages */
if ($page === 'login') {
    if (is_logged_in()) redirect(admin_url('dashboard'));
    render_standalone('login');
    exit;
}
if ($page === 'logout') {
    logout();
    redirect(admin_url('login'));
    exit;
}
if ($page === 'setup') {
    if (!$noUsers) redirect(admin_url('login'));
    render_standalone('setup');
    exit;
}

/* ------------------------------------------------ authenticated views */
require_login();

$view = __DIR__ . '/views/' . $page . '.php';
if (!is_file($view)) {
    http_response_code(404);
    render('dashboard', ['title' => 'Dashboard']);
    exit;
}

// Per-page permission gate (defense in depth; buttons also hide).
$page_perms = [
    'dashboard' => 'activity', 'projects' => 'projects', 'project_edit' => 'projects',
    'media' => 'media', 'journal' => 'journal',
    'pages' => 'pages', 'nav' => 'nav', 'seo' => 'seo',
    'inquiries' => 'inquiries', 'users' => 'users', 'settings' => 'settings',
    'activity' => 'activity', 'revisions' => 'projects',
];
$need = $page_perms[$page] ?? 'activity';
if (!can($need)) {
    http_response_code(403);
    die('Forbidden: your role does not allow this page.');
}

$vars = page_data($page);
render($page, $vars);

/* ------------------------------------------------ helpers */

/** Gather data a view needs. */
function page_data(string $page): array {
    $u = current_user();
    switch ($page) {
        case 'dashboard': {
            $c = content_load();
            $site = site_load();
            $counts = project_counts($c);
            $pdo = cms_pdo();
            $unread = (int)$pdo->query("SELECT COUNT(*) FROM inquiries WHERE read=0")->fetchColumn();
            $recent = $pdo->query("SELECT a.*, u.name AS user_name FROM activity_log a LEFT JOIN users u ON u.id=a.user_id ORDER BY a.id DESC LIMIT 8")->fetchAll();
            $media = array_slice(media_list(), 0, 6);
            return [
                'title' => 'Dashboard', 'user' => $u, 'counts' => $counts,
                'journal_count' => count(journal_list($site)), 'unread' => $unread,
                'recent' => $recent, 'media' => $media, 'build_status' => build_supports_status(),
            ];
        }
        case 'projects': {
            $c = content_load();
            return ['title' => 'Projects', 'user' => $u, 'groups' => $c['groups']];
        }
        case 'project_edit': {
            $c = content_load();
            $id = $_GET['id'] ?? '';
            $g = $id !== '' ? group_by_id($c, $id) : null;
            if ($id !== '' && !$g) { flash('error', 'Project not found.'); redirect(admin_url('projects')); }
            return [
                'title' => $g ? 'Edit project' : 'New project', 'user' => $u,
                'group' => $g, 'all' => $c['groups'], 'media' => media_list(),
                'revisions' => $g ? revisions_for('project', $g['id']) : [],
                'number_default' => next_project_number($c),
                'build_status' => build_supports_status(),
            ];
        }
        case 'revisions': {
            $id = $_GET['id'] ?? '';
            $c = content_load();
            $g = group_by_id($c, $id);
            if (!$g) { flash('error', 'Project not found.'); redirect(admin_url('projects')); }
            return ['title' => 'Revision history', 'user' => $u, 'group' => $g, 'revisions' => revisions_for('project', $id, 25)];
        }
        case 'media': {
            return ['title' => 'Media library', 'user' => $u, 'media' => media_list()];
        }
        case 'journal': {
            $site = site_load();
            return ['title' => 'Journal', 'user' => $u, 'journal' => journal_list($site)];
        }
        case 'pages': {
            return ['title' => 'Pages & sections', 'user' => $u, 'site' => site_load(), 'media' => media_list(), 'build_disabled' => build_supports_disabled()];
        }
        case 'nav': {
            return ['title' => 'Navigation', 'user' => $u, 'site' => site_load(), 'build_disabled' => build_supports_disabled()];
        }
        case 'seo': {
            $c = content_load();
            return ['title' => 'SEO', 'user' => $u, 'site' => site_load(), 'groups' => $c['groups']];
        }
        case 'inquiries': {
            $pdo = cms_pdo();
            $rows = $pdo->query("SELECT * FROM inquiries ORDER BY id DESC")->fetchAll();
            return ['title' => 'Inquiries', 'user' => $u, 'rows' => $rows];
        }
        case 'users': {
            $rows = cms_pdo()->query("SELECT * FROM users ORDER BY id ASC")->fetchAll();
            return ['title' => 'Users', 'user' => $u, 'rows' => $rows];
        }
        case 'settings': {
            return ['title' => 'Settings', 'user' => $u, 'site' => site_load(), 'build_status' => build_supports_status()];
        }
        case 'activity': {
            $rows = cms_pdo()->query("SELECT a.*, u.name AS user_name FROM activity_log a LEFT JOIN users u ON u.id=a.user_id ORDER BY a.id DESC LIMIT 200")->fetchAll();
            return ['title' => 'Activity log', 'user' => $u, 'rows' => $rows];
        }
        default:
            return ['title' => 'Dashboard', 'user' => $u];
    }
}

function render(string $view, array $vars = []): void {
    extract($vars, EXTR_SKIP);
    try {
        $GLOBALS['__unread'] = (int)cms_pdo()->query("SELECT COUNT(*) FROM inquiries WHERE read=0")->fetchColumn();
    } catch (Throwable $t) { $GLOBALS['__unread'] = 0; }
    ob_start();
    require __DIR__ . '/views/' . $view . '.php';
    $content = ob_get_clean();
    require __DIR__ . '/views/layout.php';
}

function render_standalone(string $view): void {
    $vars = ['title' => $view === 'setup' ? 'First-run setup' : 'Sign in'];
    extract($vars, EXTR_SKIP);
    require __DIR__ . '/views/' . $view . '.php';
}
