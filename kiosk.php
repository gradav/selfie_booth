<?php
/**
 * Dynamic Kiosk Router
 * Handles URL routing for /selfie_booth/1, /selfie_booth/2, etc.
 * Manages kiosk checkout/assignment system
 */

// Error reporting for debugging
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Get the kiosk ID from URL parameter
$kiosk_id = isset($_GET['kiosk_id']) ? intval($_GET['kiosk_id']) : 0;

// Validate kiosk ID range (1-50)
if ($kiosk_id < 1 || $kiosk_id > 50) {
    http_response_code(400);
    showError("Invalid kiosk number. Please use a number between 1 and 50.");
    exit;
}

// Configuration
$KIOSK_STATUS_FILE = __DIR__ . '/api/kiosk_status.json';
$SESSION_TIMEOUT = 30 * 60; // 30 minutes in seconds

/**
 * Load kiosk status from file
 */
function loadKioskStatus() {
    global $KIOSK_STATUS_FILE;
    
    if (!file_exists($KIOSK_STATUS_FILE)) {
        // Initialize with all kiosks available
        $status = [];
        for ($i = 1; $i <= 50; $i++) {
            $status[$i] = [
                'status' => 'available',
                'assigned_at' => null,
                'session_id' => null,
                'location' => getDefaultLocation($i)
            ];
        }
        saveKioskStatus($status);
        return $status;
    }
    
    $json = file_get_contents($KIOSK_STATUS_FILE);
    return json_decode($json, true) ?: [];
}

/**
 * Save kiosk status to file
 */
function saveKioskStatus($status) {
    global $KIOSK_STATUS_FILE;
    
    // Ensure directory exists
    $dir = dirname($KIOSK_STATUS_FILE);
    if (!is_dir($dir)) {
        mkdir($dir, 0755, true);
    }
    
    file_put_contents($KIOSK_STATUS_FILE, json_encode($status, JSON_PRETTY_PRINT));
}

/**
 * Get default location for kiosk number
 */
function getDefaultLocation($kiosk_id) {
    $locations = [
        1 => 'lobby',
        2 => 'entrance', 
        3 => 'event_hall',
        4 => 'party_room'
    ];
    
    return $locations[$kiosk_id] ?? "kiosk_$kiosk_id";
}

/**
 * Check if a kiosk session has expired
 */
function isSessionExpired($assigned_at) {
    global $SESSION_TIMEOUT;
    
    if (!$assigned_at) return false;
    
    return (time() - $assigned_at) > $SESSION_TIMEOUT;
}

/**
 * Clean up expired sessions
 */
function cleanupExpiredSessions(&$status) {
    foreach ($status as $id => &$kiosk) {
        if ($kiosk['status'] === 'in_use' && isSessionExpired($kiosk['assigned_at'])) {
            $kiosk['status'] = 'available';
            $kiosk['assigned_at'] = null;
            $kiosk['session_id'] = null;
        }
    }
}

/**
 * Try to checkout a kiosk
 */
function checkoutKiosk($kiosk_id, &$status) {
    if (!isset($status[$kiosk_id])) {
        return false;
    }
    
    $kiosk = &$status[$kiosk_id];
    
    // Check if available or expired
    if ($kiosk['status'] === 'available' || isSessionExpired($kiosk['assigned_at'])) {
        $session_id = 'session_' . $kiosk_id . '_' . time();
        
        $kiosk['status'] = 'in_use';
        $kiosk['assigned_at'] = time();
        $kiosk['session_id'] = $session_id;
        
        return $session_id;
    }
    
    return false;
}

/**
 * Show error page
 */
function showError($message) {
    ?>
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Kiosk Error</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin: 50px; }
            .error { color: #e74c3c; background: #ffeaea; padding: 20px; border-radius: 8px; }
            .back-btn { margin-top: 20px; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="error">
            <h2>Kiosk Error</h2>
            <p><?php echo htmlspecialchars($message); ?></p>
            <a href="/selfie_booth/" class="back-btn">Back to Home</a>
        </div>
    </body>
    </html>
    <?php
}

/**
 * Show kiosk in use page
 */
function showKioskInUse($kiosk_id, $time_remaining) {
    ?>
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Kiosk In Use</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin: 50px; }
            .in-use { color: #f39c12; background: #fef9e7; padding: 20px; border-radius: 8px; }
            .suggestion { margin: 20px 0; color: #2c3e50; }
            .try-btn { margin: 10px; padding: 10px 20px; background: #27ae60; color: white; text-decoration: none; border-radius: 5px; }
            .home-btn { margin: 10px; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="in-use">
            <h2>📱 Kiosk <?php echo $kiosk_id; ?> is Currently In Use</h2>
            <p>This kiosk is being used by another guest.</p>
            <?php if ($time_remaining > 0): ?>
                <p>It will be available in approximately <?php echo ceil($time_remaining / 60); ?> minutes.</p>
            <?php endif; ?>
            
            <div class="suggestion">
                <h3>Try these available kiosks:</h3>
                <?php
                // Show some available alternatives
                $alternatives = [1, 2, 3, 4, 5];
                foreach ($alternatives as $alt) {
                    if ($alt != $kiosk_id) {
                        echo "<a href='/selfie_booth/$alt' class='try-btn'>Try Kiosk $alt</a>";
                    }
                }
                ?>
            </div>
            
            <div>
                <a href="/selfie_booth/" class="home-btn">Back to Home</a>
                <a href="/selfie_booth/<?php echo $kiosk_id; ?>" class="try-btn">Try Again</a>
            </div>
        </div>
    </body>
    </html>
    <?php
}

// Main logic
try {
    // Load current kiosk status
    $status = loadKioskStatus();
    
    // Clean up expired sessions
    cleanupExpiredSessions($status);
    
    // Try to checkout the requested kiosk
    $session_id = checkoutKiosk($kiosk_id, $status);
    
    if ($session_id) {
        // Success! Save status and redirect to mobile.html
        saveKioskStatus($status);
        
        $tablet_id = "TABLET$kiosk_id";
        $location = $status[$kiosk_id]['location'];
        
        // Redirect to mobile.html with parameters
        $redirect_url = "/selfie_booth/mobile.html?tablet_id=$tablet_id&location=$location&kiosk_id=$kiosk_id&session_id=$session_id";
        header("Location: $redirect_url");
        exit;
        
    } else {
        // Kiosk is in use, show error page
        $kiosk = $status[$kiosk_id];
        $time_remaining = $SESSION_TIMEOUT - (time() - $kiosk['assigned_at']);
        
        showKioskInUse($kiosk_id, $time_remaining);
    }
    
} catch (Exception $e) {
    error_log("Kiosk router error: " . $e->getMessage());
    showError("An error occurred. Please try again.");
}
?>