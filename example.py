#!/usr/bin/env python3
"""
Example script demonstrating CSS Analyzer usage.
"""

import sys
import os
from pathlib import Path

# Add the css_analyser directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from main import cli

if __name__ == '__main__':
    # Create sample files for demonstration
    sample_dir = Path(__file__).parent / 'sample_project'
    sample_dir.mkdir(exist_ok=True)
    
    # Create sample CSS file
    sample_css = sample_dir / 'style.css'
    sample_css.write_text("""
/* Responsive adjustments */
@media (max-width: 768px) {
    .mdt-refill-options-row {
        flex-direction: column;
        gap: 20px;
    }
    
    .mdt-refill-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 8px;
    }
    
    .mdt-refill-colors,
    .mdt-refill-diameters {
        flex-direction: row;
        flex-wrap: wrap;
        gap: 8px;
    }
    
    .mdt-color-option,
    .mdt-diameter-option {
        flex: 0 0 auto;
    }
}
/* Cart item display enhancements */
.mdt-cart-print-item,
.mdt-cart-refill-item {
    margin: 8px 0;
    padding: 12px;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    background: #f9f9f9;
    font-size: 0.9em;
}
.mdt-cart-logo-info,
.mdt-cart-preview-info {
    margin-top: 4px;
}
.mdt-cart-logo-info small,
.mdt-cart-preview-info small {
    color: #666;
    font-size: 0.8em;
}
.mdt-cart-refill-info {
    font-size: 0.85em;
    color: #666;
    font-style: italic;
    margin-top: 4px;
}
.mdt-color-dot {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 1px solid #ccc;
    margin-right: 4px;
    vertical-align: middle;
}
/* Style for color dots in refill display */
.mdt-refill-color-dot {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 1px solid #ccc;
    margin-right: 4px;
    vertical-align: middle;
}
/* WooCommerce cart table compatibility */
.cart_item .woocommerce-cart-form__cart-item .mdt-cart-print-item,
.cart_item .woocommerce-cart-form__cart-item .mdt-cart-refill-item {
    margin: 5px 0;
    font-size: 0.85em;
}
/* Mini cart compatibility */
.woocommerce-mini-cart .mdt-cart-print-item,
.woocommerce-mini-cart .mdt-cart-refill-item {
    margin: 3px 0;
    padding: 8px;
    font-size: 0.8em;
}
/*
 * Enhanced Styles for Multi-Tier Druck Pricing Plugin v2.0
 */
.mdt-container {
    border: 1px solid #e0e0e0;
    padding: 20px;
    margin-bottom: 20px;
    border-radius: 8px;
    background-color: #fafafa;
}
.mdt-container h3,
.mdt-container h4 {
    margin-top: 0;
    margin-bottom: 15px;
    color: #333;
}
/* B2B Order Splitter Admin Styles */
/* Meta Box Styling */
.bos-child-orders-list {
    margin: 10px 0;
}
.bos-child-orders-list table {
    border-collapse: collapse;
    width: 100%;
}
.bos-child-orders-list th {
    background-color: #f8f9fa;
    font-weight: 600;
    padding: 10px;
    text-align: left;
    border: 1px solid #ddd;
}
.bos-child-orders-list td {
    padding: 10px;
    border: 1px solid #ddd;
}
.bos-child-orders-list tr:nth-child(even) {
    background-color: #f9f9f9;
}
/* Parent Order Info Styling */
.bos-parent-order-info {
    background-color: #f0f8ff;
    border-left: 4px solid #0073aa;
    padding: 15px;
    margin: 10px 0;
}
.bos-parent-order-info p {
    margin: 5px 0;
}
.bos-parent-order-info strong {
    color: #333;
}
""")
    
    # Create sample HTML file
    sample_html = sample_dir / 'index.html'
    sample_html.write_text("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sample Page</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="mdt-container">
        <h3>Sample Container</h3>
        <div class="mdt-cart-print-item">
            <div class="mdt-cart-logo-info">
                <small>Logo info</small>
            </div>
            <div class="mdt-cart-refill-info">
                Refill information
            </div>
        </div>
        
        <div class="bos-parent-order-info">
            <p><strong>Parent Order:</strong> #12345</p>
            <p>Order details go here</p>
        </div>
        
        <div class="bos-child-orders-list">
            <table>
                <thead>
                    <tr>
                        <th>Order ID</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>#12346</td>
                        <td>Processing</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <div class="mdt-refill-options-row">
        <div class="mdt-refill-header">
            <h4>Refill Options</h4>
        </div>
        <div class="mdt-refill-colors">
            <div class="mdt-color-option">
                <span class="mdt-color-dot"></span>
                Red
            </div>
        </div>
    </div>
</body>
</html>
""")
    
    # Create sample JS file
    sample_js = sample_dir / 'script.js'
    sample_js.write_text("""
jQuery(function ($) {
    'use strict';
    const appContainer = $('#mdt-druck-pricing-app');
    if (!appContainer.length) {
        return;
    }
    // Parse both data sets
    const druckInfoData = JSON.parse($('#mdt-druck-info-data').text() || '{}'); // General pricing data
    const variantPositionsData = JSON.parse($('#mdt-variant-positions-data').text() || '{}'); // Variant positions
    // const refillInfoData = JSON.parse($('#mdt-refill-info-data').text() || '[]'); // Refill options data
    
    let selectedDrucks = {};
    let selectedRefill = null;
    let druckCounter = 0;
    let currentVariationData = null;
    // Create individual refill card with proper styling
    function createRefillCard(refill, refillId, isSelected = false) {
        const hasInfo = refill.info && refill.info.trim();
        const hasPrice = refill.price && refill.price > 0;
        const hasColors = refill.colors && refill.colors.length > 0;
        const hasDiameters = refill.diameter && refill.diameter.length > 0;
        
        let refillCardHtml = `
            <div class="mdt-refill-card ${isSelected ? 'mdt-refill-selected' : ''}" data-refill-id="${refillId}">
                <div class="mdt-refill-header">
                    <div class="mdt-refill-title">
                        <div class="mdt-refill-radio-wrapper">
                            <input type="radio" name="selected_refill" value="${refillId}" ${isSelected ? 'checked' : ''} 
                                   class="mdt-refill-radio" id="radio_${refillId}">
                            <span class="mdt-refill-radio-dot"></span>
                        </div>
                        <label for="radio_${refillId}" class="mdt-refill-label">${refill.label}</label>
                    </div>
                    ${hasPrice ? `<div class="mdt-refill-price">+${formatPrice(refill.price)}</div>` : ''}
                </div>
        `;
        
        if (hasInfo) {
            refillCardHtml += `<div class="mdt-refill-info">${refill.info}</div>`;
        }
        
        if (hasColors || hasDiameters) {
            refillCardHtml += '<div class="mdt-refill-options-row">';
            
            // Colors section
            if (hasColors) {
                refillCardHtml += `
                    <div class="mdt-refill-section">
                        <h5 class="mdt-refill-section-title">Minenfarbe</h5>
                        <div class="mdt-refill-colors">`;
                
                refill.colors.forEach((color, colorIndex) => {
                    const isFirstColor = colorIndex === 0;
                    const isDisabled = !isSelected;
                    refillCardHtml += `
                        <label class="mdt-color-option ${isFirstColor && isSelected ? 'mdt-color-selected' : ''} ${isDisabled ? 'mdt-color-disabled' : ''}">
                            <input type="radio" name="${refillId}_color" value="${colorIndex}" 
                                   ${isFirstColor ? 'checked' : ''} ${isDisabled ? 'disabled' : ''} 
                                   class="mdt-color-radio">
                            <span class="mdt-color-swatch" style="background-color: ${color.hex}"></span>
                            <span class="mdt-color-label">${color.label}</span>
                        </label>
                    `;
                });
                
                refillCardHtml += '</div></div>';
            }
            
            // Diameters section
            if (hasDiameters) {
                refillCardHtml += `
                    <div class="mdt-refill-section">
                        <h5 class="mdt-refill-section-title">Durchmesser</h5>
                        <div class="mdt-refill-diameters">`;
                
                refill.diameter.forEach((diameter, diameterIndex) => {
                    const isFirstDiameter = diameterIndex === 0;
                    const isDisabled = !isSelected;
                    const diameterPrice = diameter.price ? ` (+${formatPrice(diameter.price)})` : '';
                    refillCardHtml += `
                        <label class="mdt-diameter-option ${isFirstDiameter && isSelected ? 'mdt-diameter-selected' : ''} ${isDisabled ? 'mdt-diameter-disabled' : ''}">
                            <input type="radio" name="${refillId}_diameter" value="${diameterIndex}" 
                                   ${isFirstDiameter ? 'checked' : ''} ${isDisabled ? 'disabled' : ''} 
                                   class="mdt-diameter-radio">
                            <span class="mdt-diameter-dot"></span>
                            <span class="mdt-diameter-label">${diameter.label}${diameterPrice}</span>
                        </label>
                    `;
                });
                
                refillCardHtml += '</div></div>';
            }
            
            refillCardHtml += '</div>';
        }
        
        refillCardHtml += '</div>';
        return refillCardHtml;
    }
});
""")
    
    # Create sample PHP file
    sample_php = sample_dir / 'index.php'
    sample_php.write_text("""<?php
if ( ! defined( 'ABSPATH' ) ) {
    exit;
}
/**
 * Class MDT_Frontend
 *
 * Handles the display of the UI on the single product page.
 */
class MDT_Frontend {
    private static $_instance = null;
    public static function instance() {
        if ( is_null( self::$_instance ) ) {
            self::$_instance = new self();
        }
        return self::$_instance;
    }
    private function __construct() {
        // Hook to add our custom UI elements to the product page
        add_action( 'woocommerce_before_add_to_cart_button', [ $this, 'render_druck_ui' ], 20 );
        // Enqueue scripts and styles
        add_action( 'wp_enqueue_scripts', [ $this, 'enqueue_assets' ] );
    }

    /**
     * Render the new druck options interface
     * UPDATED: Use variant positions for UI, general info for data
     */
    private function render_druck_options_interface( $druck_info_list ) {
        global $product;
        $plugin_class = MDT_Plugin::instance();
        // Get variant-specific positions for UI display
        $variant_positions = $plugin_class->get_variant_print_positions( $product );
        
        ?>
        <div class="mdt-druck-options-interface mdt-card">
            <h3><?php _e('Druckoptionen auswählen', 'multi-tier-druck-pricing'); ?></h3>
            <?php if ( $product->is_type('variable') ): ?>
                <!-- Show message for variable products -->
                <div class="mdt-variant-selection-notice">
                    <p><?php _e('Bitte wählen Sie zuerst eine Produktvariante aus, um die verfügbaren Druckoptionen zu sehen.', 'multi-tier-druck-pricing'); ?></p>
                </div>
            <?php endif; ?>
            <div class="mdt-druck-selector" <?php echo $product->is_type('variable') ? 'style="display:none;"' : ''; ?>>
                <div class="mdt-add-druck-section">
                    <div class="mdt-select-wrapper">
                        <label for="mdt-druck-select"><?php _e('Druckoption wählen:', 'multi-tier-druck-pricing'); ?></label>
                        <select id="mdt-druck-select" <?php echo empty($variant_positions) ? 'disabled' : ''; ?>>
                            <option value=""><?php _e('-- Druckoption wählen --', 'multi-tier-druck-pricing'); ?></option>
                            <?php
                            foreach ( $variant_positions as $position_key => $position_info ) {
                                // TODO: for any updates also update updateDruckSelectOptions() in frontend.js
                                // Find the matching druck_info by code
                                $druck_info = null;
                                foreach ( $druck_info_list as $info ) {
                                    if ( isset($info['code']) && $info['code'] === $position_info['code'] ) {
                                        $druck_info = $info;
                                        break;
                                    }
                                }
                                // Only show if matching druck_info found
                                if ( $druck_info ) {
                                    ?>
                                    <option value="<?php echo esc_attr($position_key); ?>"
                                            data-druck-label="<?php echo esc_attr($position_info['druck_label']); ?>"
                                            data-length="<?php echo esc_attr($position_info['length']); ?>"
                                            data-height="<?php echo esc_attr($position_info['height']); ?>"
                                            data-max-colors="<?php echo esc_attr($position_info['max_colors']); ?>"
                                            data-code="<?php echo esc_attr($position_info['code']); ?>"
                                            data-supplier="<?php echo esc_attr($position_info['supplier']); ?>">
                                        <?php echo esc_html($position_info['druck_label']); ?> (<?php echo esc_html($position_info['length']); ?>x<?php echo esc_html($position_info['height']); ?>mm) (<?php echo esc_html($druck_info['druck_label']); ?>)
                                    </option>
                                    <?php
                                }
                            }
                            ?>
                        </select>
                    </div>
                    <button type="button" id="mdt-add-druck-btn" class="button" <?php echo empty($variant_positions) ? 'disabled' : ''; ?>>
                        <span class="dashicons dashicons-plus-alt2"></span>
                        <?php _e('Hinzufügen', 'multi-tier-druck-pricing'); ?>
                    </button>
                </div>
            </div>
            <div id="mdt-selected-drucks" class="mdt-selected-prints">
                <h4><?php _e('Gewählte Druckoptionen', 'multi-tier-druck-pricing'); ?></h4>
                <div class="mdt-drucks-list-container">
                    <div id="mdt-drucks-list" class="mdt-drucks-list">
                        <p class="mdt-no-drucks"><?php _e('Keine Druckoptionen gewählt.', 'multi-tier-druck-pricing'); ?></p>
                    </div>
                </div>
            </div>
            <!-- Hidden inputs for form submission -->
            <div id="mdt-hidden-inputs"></div>
        </div>
        
        <!-- Both data sets for JavaScript -->
        <script type="application/json" id="mdt-druck-info-data">
            <?php echo json_encode($druck_info_list); ?>
        </script>
        <script type="application/json" id="mdt-variant-positions-data">
            <?php echo json_encode($variant_positions); ?>
        </script>
        <?php
    }
}
""")
    
    print("Sample project created successfully!")
    print(f"Sample files created in: {sample_dir}")
    print("\nYou can now test the CSS analyzer with these commands:")
    print(f"python -m css_analyser.main duplicates {sample_dir}")
    print(f"python -m css_analyser.main unused {sample_dir}")
    print(f"python -m css_analyser.main structure {sample_dir}")
    print(f"python -m css_analyser.main analyze {sample_dir} --output-html report.html")