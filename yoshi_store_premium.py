import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
import io
import json
from datetime import datetime
import base64

# ═════════════════════════════════════════════════════════════════════════════
# DATABASE SETUP WITH ENHANCED SCHEMA
# ═════════════════════════════════════════════════════════════════════════════

DB_FILE = "yoshi_premium.db"

def init_db():
    """Initialize database with new hierarchical category structure"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Brand Settings Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS brand_settings (
            id INTEGER PRIMARY KEY,
            brand_name TEXT DEFAULT 'Yoshi',
            tagline TEXT DEFAULT 'Pure Handcrafted Organic Goodness',
            primary_color TEXT DEFAULT '#1b3c22',
            secondary_color TEXT DEFAULT '#f7cb65',
            background_color TEXT DEFAULT '#fcfbf7',
            logo_text TEXT DEFAULT '🌿 YOSHI 🍯',
            about_text TEXT
        )
    ''')
    
    # Categories Table (Main categories like Soap, Honey, etc.)
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            icon TEXT,
            description TEXT
        )
    ''')
    
    # Subcategories Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS subcategories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    # Enhanced Products Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subcategory_id INTEGER,
            title TEXT NOT NULL,
            ingredients TEXT,
            regular_price REAL NOT NULL,
            sale_price REAL,
            rating REAL DEFAULT 4.8,
            reviews_count INTEGER DEFAULT 50,
            description TEXT,
            benefits TEXT,
            badge TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subcategory_id) REFERENCES subcategories(id)
        )
    ''')
    
    # Product Images Table (Support multiple images)
    c.execute('''
        CREATE TABLE IF NOT EXISTS product_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            image_data BLOB NOT NULL,
            alt_text TEXT,
            is_primary BOOLEAN DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    
    # Orders Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            customer_email TEXT,
            customer_phone TEXT,
            address TEXT,
            city TEXT,
            pincode TEXT,
            items_summary TEXT,
            total_amount REAL,
            payment_method TEXT,
            status TEXT,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Check if brand settings exist
    c.execute("SELECT COUNT(*) FROM brand_settings")
    if c.fetchone()[0] == 0:
        c.execute('''
            INSERT INTO brand_settings (brand_name, tagline, about_text)
            VALUES (?, ?, ?)
        ''', ('Yoshi', 'Pure Handcrafted Organic Goodness', 
              'Founded on the promise to deliver pure, handcrafted organic goods from nature directly to your home.'))
    
    # Seed sample categories and products if empty
    c.execute("SELECT COUNT(*) FROM categories")
    if c.fetchone()[0] == 0:
        # Add main categories
        categories = [
            ("Herbal Soaps", "🧼", "Handcrafted organic soaps with natural oils"),
            ("Face Pack Powders", "🌸", "Traditional herbal face pack powders"),
            ("Organic Honey", "🍯", "100% Pure forest honey with superfoods"),
            ("Hair Care", "💇", "Natural hair oils and care products"),
            ("Serums & Oils", "✨", "Concentrated plant extracts and oils")
        ]
        for cat_name, icon, desc in categories:
            c.execute("INSERT INTO categories (name, icon, description) VALUES (?, ?, ?)", 
                     (cat_name, icon, desc))
        
        # Add subcategories for Soaps
        c.execute("INSERT INTO subcategories (category_id, name, description) VALUES (?, ?, ?)",
                 (1, "Charcoal & Neem Soaps", "Deep cleansing activated charcoal soaps"))
        c.execute("INSERT INTO subcategories (category_id, name, description) VALUES (?, ?, ?)",
                 (1, "Honey & Almond Soaps", "Moisturizing gentle soaps"))
        c.execute("INSERT INTO subcategories (category_id, name, description) VALUES (?, ?, ?)",
                 (1, "Turmeric Soaps", "Traditional turmeric and herb soaps"))
        
        # Add subcategories for Face Packs
        c.execute("INSERT INTO subcategories (category_id, name, description) VALUES (?, ?, ?)",
                 (2, "Turmeric & Sandalwood", "Traditional face packs for glow"))
        c.execute("INSERT INTO subcategories (category_id, name, description) VALUES (?, ?, ?)",
                 (2, "Neem & Basil Packs", "Acne-fighting herbal powders"))
        c.execute("INSERT INTO subcategories (category_id, name, description) VALUES (?, ?, ?)",
                 (2, "Clay & Herb Packs", "Detoxifying face packs"))
        
        # Add subcategories for Honey
        c.execute("INSERT INTO subcategories (category_id, name, description) VALUES (?, ?, ?)",
                 (3, "Raw Forest Honey", "Pure unprocessed honey"))
        c.execute("INSERT INTO subcategories (category_id, name, description) VALUES (?, ?, ?)",
                 (3, "Infused Honey", "Honey with superfoods and herbs"))
        
        # Add sample products
        sample_products = [
            (1, "Yoshi Charcoal & Neem Deep Cleansing Soap", 
             "Activated Bamboo Charcoal, Pure Neem Extract, Virgin Coconut Oil",
             199.0, 149.0, "Handcrafted organic soap that deeply purifies and treats body acne.",
             "Removes impurities, Treats acne, Moisturizes skin, Safe for all skin types",
             "Handcrafted 🧼"),
            (2, "Yoshi Nourishing Honey & Almond Goat Milk Soap",
             "Raw Honey, Sweet Almond Oil, Organic Goat Milk",
             220.0, 169.0, "Gentle and moisturizing soap, perfect for sensitive skin.",
             "Gentle on sensitive skin, Deeply moisturizes, Safe for kids and elders",
             "Made Safe Certified 🛡️"),
            (3, "Yoshi Turmeric & Sandalwood Soap",
             "Kasturi Manjal, Sandalwood, Natural Oils",
             189.0, 139.0, "Traditional turmeric soap for radiant skin.",
             "Brightens complexion, Reduces scars, Ancient recipe",
             "Traditional 🌿"),
            (4, "Yoshi Wild Turmeric & Sandalwood Face Pack Powder",
             "Kasturi Manjal, Pure Sandalwood Bark, Multani Mitti",
             349.0, 279.0, "Traditional herbal face pack for clear skin.",
             "Clears blemishes, Controls oil, Restores glow, 100% Natural",
             "Traditional Recipe 🌸"),
            (5, "Yoshi Neem, Basil & Mint Acne Repair Face Pack",
             "Sun-Dried Neem, Holy Basil, Fresh Mint",
             299.0, 239.0, "Herbal powder to fight acne and detoxify.",
             "Fights acne, Cools irritated skin, Detoxifies, Soothing",
             "100% Natural 🍃"),
            (7, "Yoshi Organic Raw Saffron Honey",
             "100% Pure Forest Honey, Kashmiri Saffron Threads",
             550.0, 480.0, "Directly from organic beehives with premium saffron.",
             "Immunity booster, Pure forest honey, Natural sweetness, Energy enhancer",
             "Best Seller 🍯"),
        ]
        
        for subcat_id, title, ingredients, reg_price, sale_price, desc, benefits, badge in sample_products:
            c.execute('''
                INSERT INTO products (subcategory_id, title, ingredients, regular_price, sale_price, description, benefits, badge)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (subcat_id, title, ingredients, reg_price, sale_price, desc, benefits, badge))
    
    conn.commit()
    conn.close()

init_db()

# ═════════════════════════════════════════════════════════════════════════════
# DATABASE HELPER FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════

def get_brand_settings():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM brand_settings WHERE id = 1")
    row = c.fetchone()
    conn.close()
    if row:
        return {
            'brand_name': row[1],
            'tagline': row[2],
            'primary_color': row[3],
            'secondary_color': row[4],
            'background_color': row[5],
            'logo_text': row[6],
            'about_text': row[7]
        }
    return {}

def update_brand_settings(brand_name, tagline, primary_color, secondary_color, background_color, logo_text, about_text):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        UPDATE brand_settings 
        SET brand_name=?, tagline=?, primary_color=?, secondary_color=?, background_color=?, logo_text=?, about_text=?
        WHERE id = 1
    ''', (brand_name, tagline, primary_color, secondary_color, background_color, logo_text, about_text))
    conn.commit()
    conn.close()

def get_categories():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT id, name, icon, description FROM categories ORDER BY name", conn)
    conn.close()
    return df

def get_subcategories(category_id=None):
    conn = sqlite3.connect(DB_FILE)
    if category_id:
        df = pd.read_sql_query(
            "SELECT id, category_id, name, description FROM subcategories WHERE category_id = ? ORDER BY name",
            conn, params=[category_id]
        )
    else:
        df = pd.read_sql_query(
            "SELECT id, category_id, name, description FROM subcategories ORDER BY name", conn
        )
    conn.close()
    return df

def get_products(category_id=None, subcategory_id=None, search_query=None):
    conn = sqlite3.connect(DB_FILE)
    query = "SELECT p.id, p.subcategory_id, p.title, p.ingredients, p.regular_price, p.sale_price, p.rating, p.reviews_count, p.description, p.benefits, p.badge, s.name as subcategory_name, c.name as category_name FROM products p LEFT JOIN subcategories s ON p.subcategory_id = s.id LEFT JOIN categories c ON s.category_id = c.id WHERE 1=1"
    params = []
    
    if category_id:
        query += " AND c.id = ?"
        params.append(category_id)
    if subcategory_id:
        query += " AND p.subcategory_id = ?"
        params.append(subcategory_id)
    if search_query:
        query += " AND (p.title LIKE ? OR p.ingredients LIKE ? OR p.description LIKE ? OR p.benefits LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])
    
    df = pd.read_sql_query(query + " ORDER BY p.id DESC", conn, params=params)
    conn.close()
    return df

def get_product_images(product_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, image_data, alt_text, is_primary FROM product_images WHERE product_id = ? ORDER BY is_primary DESC, id", (product_id,))
    images = c.fetchall()
    conn.close()
    return images

def add_product(subcategory_id, title, ingredients, reg_price, sale_price, description, benefits, badge):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO products (subcategory_id, title, ingredients, regular_price, sale_price, description, benefits, badge)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (subcategory_id, title, ingredients, reg_price, sale_price, description, benefits, badge))
    product_id = c.lastrowid
    conn.commit()
    conn.close()
    return product_id

def add_product_image(product_id, image_bytes, alt_text="", is_primary=False):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO product_images (product_id, image_data, alt_text, is_primary)
        VALUES (?, ?, ?, ?)
    ''', (product_id, image_bytes, alt_text, is_primary))
    conn.commit()
    conn.close()

def update_product(product_id, title, ingredients, reg_price, sale_price, description, benefits, badge):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        UPDATE products 
        SET title=?, ingredients=?, regular_price=?, sale_price=?, description=?, benefits=?, badge=?
        WHERE id=?
    ''', (title, ingredients, reg_price, sale_price, description, benefits, badge, product_id))
    conn.commit()
    conn.close()

def delete_product(product_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM product_images WHERE product_id=?", (product_id,))
    c.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()

def add_category(name, icon, description):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO categories (name, icon, description) VALUES (?, ?, ?)", (name, icon, description))
    conn.commit()
    conn.close()

def add_subcategory(category_id, name, description):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO subcategories (category_id, name, description) VALUES (?, ?, ?)", (name, description, category_id))
    conn.commit()
    conn.close()

def save_order(name, email, phone, address, city, pincode, items_summary, total_amount, payment_method):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO orders (customer_name, customer_email, customer_phone, address, city, pincode, items_summary, total_amount, payment_method, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, email, phone, address, city, pincode, items_summary, total_amount, payment_method, "Order Confirmed ✅"))
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id

def get_orders():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM orders ORDER BY order_date DESC", conn)
    conn.close()
    return df

def update_order_status(order_id, status):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()
    conn.close()

# ═════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG & STYLING
# ═════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="Yoshi - Premium Organic Wellness",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get brand settings
brand = get_brand_settings()

# ═════════════════════════════════════════════════════════════════════════════
# PREMIUM CSS STYLING
# ═════════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<style>
    :root {{
        --primary: {brand['primary_color']};
        --secondary: {brand['secondary_color']};
        --bg: {brand['background_color']};
        --text-dark: #1a1a1a;
        --text-light: #6b6b6b;
        --border: #e8e4dc;
        --success: #2e7d32;
    }}
    
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    
    html, body {{
        background-color: var(--bg);
        color: var(--text-dark);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        line-height: 1.6;
    }}
    
    /* TYPOGRAPHY */
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Georgia', 'Garamond', serif;
        color: var(--primary);
        font-weight: 700;
        letter-spacing: -0.5px;
    }}
    
    h1 {{ font-size: 3.5rem; line-height: 1.2; }}
    h2 {{ font-size: 2.2rem; margin: 1.5rem 0 1rem 0; }}
    h3 {{ font-size: 1.5rem; margin: 1rem 0 0.8rem 0; }}
    h4 {{ font-size: 1.25rem; }}
    
    p {{ color: var(--text-light); margin-bottom: 0.8rem; }}
    
    /* PREMIUM HERO BANNER */
    .hero-banner {{
        background: linear-gradient(135deg, var(--primary) 0%, #{hex(int(brand['primary_color'][1:], 16) - 0x111111)[2:].zfill(6)} 100%);
        color: white;
        padding: 60px 40px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 50px;
        box-shadow: 0 20px 60px rgba(27, 60, 34, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.1);
        position: relative;
        overflow: hidden;
    }}
    
    .hero-banner::before {{
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 70%);
        border-radius: 50%;
    }}
    
    .hero-logo {{
        font-size: 4rem;
        font-weight: 800;
        margin-bottom: 15px;
        text-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        letter-spacing: 1px;
    }}
    
    .hero-tagline {{
        font-size: 1.35rem;
        color: rgba(255, 255, 255, 0.95);
        font-weight: 300;
        margin-bottom: 10px;
    }}
    
    /* PRODUCT CARDS */
    .product-card {{
        background: white;
        border-radius: 16px;
        border: 1px solid var(--border);
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        display: flex;
        flex-direction: column;
        height: 100%;
    }}
    
    .product-card:hover {{
        transform: translateY(-8px);
        box-shadow: 0 12px 35px rgba(27, 60, 34, 0.12);
        border-color: var(--primary);
    }}
    
    .product-image-container {{
        position: relative;
        width: 100%;
        height: 300px;
        background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
        overflow: hidden;
    }}
    
    .product-badge {{
        position: absolute;
        top: 12px;
        right: 12px;
        background: linear-gradient(135deg, var(--secondary) 0%, #{hex(int(brand['secondary_color'][1:], 16) - 0x222222)[2:].zfill(6)} 100%);
        color: var(--primary);
        padding: 6px 12px;
        border-radius: 50px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }}
    
    .product-info {{
        padding: 20px;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
    }}
    
    .product-title {{
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 8px;
        color: var(--text-dark);
        line-height: 1.4;
    }}
    
    .product-ingredients {{
        font-size: 0.85rem;
        color: var(--text-light);
        margin-bottom: 8px;
        font-style: italic;
    }}
    
    .product-rating {{
        font-size: 0.9rem;
        margin-bottom: 10px;
    }}
    
    .product-benefits {{
        font-size: 0.85rem;
        color: var(--text-light);
        margin-bottom: 12px;
        flex-grow: 1;
    }}
    
    .price-section {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 15px 0;
        border-top: 1px solid var(--border);
        padding-top: 15px;
    }}
    
    .price-original {{
        text-decoration: line-through;
        color: var(--text-light);
        font-size: 0.95rem;
    }}
    
    .price-current {{
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--primary);
    }}
    
    .discount-badge {{
        background: #fff3cd;
        color: #856404;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }}
    
    /* BUTTONS */
    .stButton>button {{
        background: linear-gradient(135deg, var(--primary) 0%, #{hex(int(brand['primary_color'][1:], 16) - 0x111111)[2:].zfill(6)} 100%);
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 28px !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(27, 60, 34, 0.2) !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(27, 60, 34, 0.3) !important;
    }}
    
    /* SIDEBAR */
    .sidebar {{
        background: linear-gradient(180deg, var(--primary) 0%, #{hex(int(brand['primary_color'][1:], 16) - 0x222222)[2:].zfill(6)} 100%);
    }}
    
    [data-testid="stSidebarNav"] {{
        background: var(--primary);
        color: white;
    }}
    
    /* DIVIDERS */
    .fancy-divider {{
        height: 3px;
        background: linear-gradient(90deg, transparent 0%, var(--primary) 50%, transparent 100%);
        margin: 30px 0;
        border-radius: 2px;
    }}
    
    /* CONTAINERS */
    .container {{
        max-width: 1200px;
        margin: 0 auto;
        padding: 0 15px;
    }}
    
    /* INFO CARDS */
    .info-box {{
        background: linear-gradient(135deg, rgba(247, 203, 101, 0.1) 0%, rgba(27, 60, 34, 0.05) 100%);
        border: 1px solid var(--secondary);
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
    }}
</style>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═════════════════════════════════════════════════════════════════════════════

if "cart" not in st.session_state:
    st.session_state.cart = {}  # {product_id: {'title': '', 'price': 0, 'qty': 0}}
if "current_page" not in st.session_state:
    st.session_state.current_page = "Shop"

# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ═════════════════════════════════════════════════════════════════════════════

st.sidebar.markdown(f"# {brand['logo_text']}")
st.sidebar.markdown(f"*{brand['tagline']}*")
st.sidebar.markdown("---")

pages = {
    "🛍️ Shop": "shop",
    "🛒 Cart": "cart",
    "📦 Orders": "orders",
    "ℹ️ About": "about",
    "⚙️ Admin": "admin"
}

selected_page = st.sidebar.radio("Navigate:", list(pages.keys()))
current_page = pages[selected_page]

cart_count = sum(item["qty"] for item in st.session_state.cart.values())
st.sidebar.markdown("---")
st.sidebar.metric("🛒 Items in Cart", cart_count)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: SHOP
# ═════════════════════════════════════════════════════════════════════════════

if current_page == "shop":
    # Hero Banner
    st.markdown(f"""
    <div class="hero-banner">
        <div class="hero-logo">{brand['logo_text']}</div>
        <div class="hero-tagline">{brand['tagline']}</div>
        <p style="margin-top: 15px; font-size: 0.95rem; color: rgba(255,255,255,0.9);">Discover the purity of nature in every product</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Search & Filter
    col1, col2 = st.columns([2, 3])
    with col1:
        categories_df = get_categories()
        selected_category = st.selectbox(
            "📂 Browse Category",
            ["All Products"] + categories_df['name'].tolist(),
            key="category_select"
        )
    with col2:
        search_term = st.text_input(
            "🔍 Search products",
            placeholder="Search by name, ingredients, or benefits..."
        )
    
    st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)
    
    # Get products
    category_id = None
    if selected_category != "All Products":
        category_id = categories_df[categories_df['name'] == selected_category]['id'].values[0]
    
    products_df = get_products(category_id=category_id, search_query=search_term if search_term else None)
    
    if products_df.empty:
        st.info("✨ No products found. Try a different search or browse all categories!")
    else:
        # Display products in a responsive grid
        cols = st.columns(3)
        for idx, (_, product) in enumerate(products_df.iterrows()):
            col = cols[idx % 3]
            
            with col:
                # Product Card
                product_images = get_product_images(product['id'])
                
                st.markdown(f"""
                <div class="product-card">
                    <div class="product-image-container">
                """, unsafe_allow_html=True)
                
                # Display primary image or placeholder
                if product_images:
                    try:
                        img = Image.open(io.BytesIO(product_images[0][1]))
                        st.image(img, use_container_width=True)
                    except:
                        st.image("https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=500&auto=format&fit=crop&q=60", use_container_width=True)
                else:
                    if "Soap" in product.get('category_name', ''):
                        st.image("https://images.unsplash.com/photo-1607006342411-91f11c888ba1?w=500&auto=format&fit=crop&q=60", use_container_width=True)
                    elif "Honey" in product.get('category_name', ''):
                        st.image("https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=500&auto=format&fit=crop&q=60", use_container_width=True)
                    elif "Face" in product.get('category_name', ''):
                        st.image("https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=500&auto=format&fit=crop&q=60", use_container_width=True)
                    else:
                        st.image("https://images.unsplash.com/photo-1540555700478-4be289fbecef?w=500&auto=format&fit=crop&q=60", use_container_width=True)
                
                # Badge
                if product['badge']:
                    st.markdown(f'<span class="product-badge">{product["badge"]}</span>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Product Info
                st.markdown(f"""
                <div class="product-info">
                    <div class="product-title">{product['title']}</div>
                    <div class="product-ingredients">🌿 {product['ingredients']}</div>
                    <div class="product-rating">⭐ {product['rating']} ({int(product['reviews_count'])} reviews)</div>
                """, unsafe_allow_html=True)
                
                if product['benefits']:
                    st.markdown(f'<div class="product-benefits">{product["benefits"]}</div>', unsafe_allow_html=True)
                
                # Pricing
                discount = 0
                if product['sale_price'] and product['regular_price'] > product['sale_price']:
                    discount = int(((product['regular_price'] - product['sale_price']) / product['regular_price']) * 100)
                
                st.markdown(f"""
                <div class="price-section">
                    <span class="price-original">₹{int(product['regular_price'])}</span>
                    <span class="price-current">₹{int(product['sale_price'])}</span>
                    {f'<span class="discount-badge">{discount}% OFF</span>' if discount > 0 else ''}
                </div>
                """, unsafe_allow_html=True)
                
                # Add to Cart Button
                if st.button(f"🛒 Add to Cart", key=f"add_{product['id']}", use_container_width=True):
                    pid = str(product['id'])
                    if pid in st.session_state.cart:
                        st.session_state.cart[pid]["qty"] += 1
                    else:
                        st.session_state.cart[pid] = {
                            "title": product['title'],
                            "price": product['sale_price'],
                            "qty": 1
                        }
                    st.success(f"✅ Added to cart!")
                    st.rerun()
                
                # Image Gallery Toggle
                if len(product_images) > 1:
                    with st.expander(f"📸 View {len(product_images)} photos"):
                        gallery_cols = st.columns(2)
                        for img_idx, (img_id, img_data, alt_text, is_primary) in enumerate(product_images):
                            try:
                                img = Image.open(io.BytesIO(img_data))
                                gallery_cols[img_idx % 2].image(img, use_container_width=True, caption=alt_text or f"Photo {img_idx + 1}")
                            except:
                                pass
                
                st.markdown('</div>', unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: SHOPPING CART & CHECKOUT
# ═════════════════════════════════════════════════════════════════════════════

elif current_page == "cart":
    st.markdown("## 🛒 Shopping Cart & Checkout")
    
    if not st.session_state.cart:
        st.info("Your cart is empty. Let's fill it with some amazing organic goodness! ✨")
        if st.button("← Continue Shopping"):
            st.session_state.current_page = "shop"
            st.rerun()
    else:
        # Cart Items
        cart_items = []
        subtotal = 0
        
        for pid, item in st.session_state.cart.items():
            item_total = item['price'] * item['qty']
            subtotal += item_total
            cart_items.append({
                "Product": item['title'],
                "Price": f"₹{int(item['price'])}",
                "Qty": item['qty'],
                "Subtotal": f"₹{int(item_total)}",
                "pid": pid
            })
        
        # Display cart table
        cart_df = pd.DataFrame(cart_items)
        st.dataframe(cart_df[["Product", "Price", "Qty", "Subtotal"]], use_container_width=True)
        
        # Manage cart
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Cart"):
                st.session_state.cart = {}
                st.success("Cart cleared!")
                st.rerun()
        with col2:
            if st.button("← Continue Shopping"):
                st.session_state.current_page = "shop"
                st.rerun()
        
        st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)
        
        # Pricing Summary
        shipping_fee = 0 if subtotal >= 399 else 49
        final_total = subtotal + shipping_fee
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Subtotal", f"₹{int(subtotal)}")
        col2.metric("Shipping", f"₹{int(shipping_fee)}")
        col3.metric("Total", f"₹{int(final_total)}")
        
        if shipping_fee > 0:
            st.info(f"💡 Add ₹{int(399 - subtotal)} more for **FREE Delivery**!")
        else:
            st.success("🎉 **FREE Delivery** - You qualify!")
        
        st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)
        
        # Checkout Form
        st.markdown("### 📦 Delivery & Payment Details")
        with st.form("checkout_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name *", placeholder="Your name")
                email = st.text_input("Email Address *", placeholder="your@email.com")
            with col2:
                phone = st.text_input("Mobile Number *", placeholder="+91 XXXXXXXXXX")
                city = st.text_input("City *", placeholder="Your city")
            
            address = st.text_area("Complete Address *", placeholder="House no., street, locality...")
            pincode = st.text_input("Pincode *", placeholder="6-digit pincode")
            
            payment = st.selectbox(
                "Payment Method",
                ["💳 Credit/Debit Card", "📱 UPI (Google Pay/PhonePe)", "💵 Cash on Delivery"]
            )
            
            submit = st.form_submit_button("🚀 Place Order", use_container_width=True)
            
            if submit:
                if not all([name, email, phone, address, city, pincode]):
                    st.error("Please fill in all required fields!")
                else:
                    items_str = ", ".join([f"{item['title']} (x{item['qty']})" for item in st.session_state.cart.values()])
                    order_id = save_order(name, email, phone, address, city, pincode, items_str, final_total, payment)
                    st.balloons()
                    st.success(f"✅ Order #YS-{order_id:04d} confirmed!")
                    st.info("📧 Confirmation sent to your email. Track your order in the Orders section!")
                    st.session_state.cart = {}
                    st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: ORDERS
# ═════════════════════════════════════════════════════════════════════════════

elif current_page == "orders":
    st.markdown("## 📦 Order Tracking & History")
    
    orders_df = get_orders()
    
    if orders_df.empty:
        st.info("No orders yet. Start shopping to see your order history here!")
    else:
        for _, order in orders_df.iterrows():
            with st.expander(f"Order #YS-{order['id']:04d} - {order['customer_name']} - {order['order_date'][:10]}", expanded=False):
                col1, col2, col3 = st.columns([2, 2, 1])
                col1.markdown(f"**Status:** {order['status']}")
                col2.markdown(f"**Amount:** ₹{int(order['total_amount'])}")
                col3.markdown(f"**Payment:** {order['payment_method']}")
                
                st.markdown(f"""
                **Items:** {order['items_summary']}
                
                **Delivery Address:** {order['address']}, {order['city']} - {order['pincode']}
                
                **Contact:** {order['customer_email']} | {order['customer_phone']}
                """)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: ABOUT
# ═════════════════════════════════════════════════════════════════════════════

elif current_page == "about":
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://images.unsplash.com/photo-1540555700478-4be289fbecef?w=500&auto=format&fit=crop&q=60", use_container_width=True)
    with col2:
        st.markdown(f"""
        ## 🌿 About {brand['brand_name']}
        
        ### Our Mission
        {brand['about_text']}
        
        ### Why Choose Us?
        - **100% Natural Ingredients** - No chemicals, no compromises
        - **Handcrafted with Love** - Each product made with care
        - **Sustainably Sourced** - Supporting local communities
        - **Trusted by Thousands** - 4.8+ star ratings
        - **Money-Back Guarantee** - Your satisfaction is our priority
        """)
    
    st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)
    
    st.markdown("### 🌟 Why Our Customers Love Us")
    col1, col2, col3 = st.columns(3)
    col1.metric("Happy Customers", "10K+")
    col2.metric("Products", "50+")
    col3.metric("Repeat Orders", "85%")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: ADMIN DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════

elif current_page == "admin":
    st.markdown("## ⚙️ Admin Dashboard")
    
    admin_tabs = st.tabs(["🎨 Brand Settings", "📂 Categories", "🛍️ Products", "📦 Orders", "🔍 Analytics"])
    
    # TAB 1: Brand Settings
    with admin_tabs[0]:
        st.markdown("### Customize Your Store Branding")
        with st.form("brand_settings_form"):
            col1, col2 = st.columns(2)
            with col1:
                brand_name = st.text_input("Brand Name", value=brand['brand_name'])
                tagline = st.text_input("Tagline", value=brand['tagline'])
                logo_text = st.text_input("Logo Text (with emojis)", value=brand['logo_text'])
                primary_color = st.color_picker("Primary Color", value=brand['primary_color'])
            with col2:
                secondary_color = st.color_picker("Secondary Color (Accent)", value=brand['secondary_color'])
                background_color = st.color_picker("Background Color", value=brand['background_color'])
                about_text = st.text_area("About Text", value=brand['about_text'], height=100)
            
            if st.form_submit_button("💾 Save Brand Settings"):
                update_brand_settings(brand_name, tagline, primary_color, secondary_color, background_color, logo_text, about_text)
                st.success("✅ Brand settings updated!")
                st.rerun()
    
    # TAB 2: Categories Management
    with admin_tabs[1]:
        st.markdown("### Manage Categories & Subcategories")
        
        subtab1, subtab2 = st.tabs(["View Categories", "Add New"])
        
        with subtab1:
            categories_df = get_categories()
            st.dataframe(categories_df, use_container_width=True)
        
        with subtab2:
            with st.form("add_category_form"):
                cat_name = st.text_input("Category Name *")
                cat_icon = st.text_input("Icon (emoji)", value="🌿")
                cat_desc = st.text_input("Description")
                
                if st.form_submit_button("Add Category"):
                    if cat_name:
                        add_category(cat_name, cat_icon, cat_desc)
                        st.success(f"✅ Added '{cat_name}' category!")
                        st.rerun()
    
    # TAB 3: Products Management
    with admin_tabs[2]:
        st.markdown("### Manage Products")
        
        ptabs = st.tabs(["View All", "Add New", "Edit", "Delete"])
        
        # View All
        with ptabs[0]:
            all_products = get_products()
            if not all_products.empty:
                st.dataframe(all_products[['id', 'title', 'category_name', 'subcategory_name', 'sale_price', 'badge']], use_container_width=True)
            else:
                st.info("No products yet!")
        
        # Add New
        with ptabs[1]:
            with st.form("add_product_form"):
                categories_df = get_categories()
                selected_cat = st.selectbox("Category", categories_df['name'].tolist())
                cat_id = categories_df[categories_df['name'] == selected_cat]['id'].values[0]
                subcats_df = get_subcategories(cat_id)
                
                if not subcats_df.empty:
                    selected_subcat = st.selectbox("Subcategory", subcats_df['name'].tolist())
                    subcat_id = subcats_df[subcats_df['name'] == selected_subcat]['id'].values[0]
                else:
                    st.warning("Please add subcategories first!")
                    subcat_id = None
                
                col1, col2 = st.columns(2)
                with col1:
                    prod_title = st.text_input("Product Title")
                    prod_ingredients = st.text_input("Ingredients/Key Actives")
                    prod_reg_price = st.number_input("Regular Price", min_value=1.0, value=299.0)
                with col2:
                    prod_sale_price = st.number_input("Sale Price", min_value=1.0, value=199.0)
                    prod_badge = st.text_input("Badge", placeholder="e.g., Best Seller 🌟")
                
                prod_desc = st.text_area("Description")
                prod_benefits = st.text_area("Benefits (comma-separated)")
                
                st.markdown("**Upload Product Images** (up to 4)")
                uploaded_files = st.file_uploader("Choose images", type=['jpg', 'jpeg', 'png', 'webp'], accept_multiple_files=True)
                
                if st.form_submit_button("Add Product"):
                    if prod_title and subcat_id:
                        prod_id = add_product(subcat_id, prod_title, prod_ingredients, prod_reg_price, prod_sale_price, prod_desc, prod_benefits, prod_badge)
                        
                        if uploaded_files:
                            for idx, file in enumerate(uploaded_files[:4]):
                                img_bytes = file.read()
                                add_product_image(prod_id, img_bytes, alt_text=f"Photo {idx+1}", is_primary=(idx==0))
                        
                        st.success(f"✅ Added '{prod_title}' with {len(uploaded_files)} images!")
                        st.rerun()
    
    # TAB 4: Orders
    with admin_tabs[3]:
        st.markdown("### Manage Customer Orders")
        orders_df = get_orders()
        
        if not orders_df.empty:
            for _, order in orders_df.iterrows():
                col1, col2, col3 = st.columns([2, 1, 1])
                col1.markdown(f"**{order['customer_name']}** - Order #YS-{order['id']:04d}")
                col2.markdown(f"₹{int(order['total_amount'])}")
                
                new_status = col3.selectbox(
                    "Status",
                    ["Order Confirmed ✅", "Processing 🔄", "Shipped 🚚", "Delivered 📦", "Cancelled ❌"],
                    index=["Order Confirmed ✅", "Processing 🔄", "Shipped 🚚", "Delivered 📦", "Cancelled ❌"].index(order['status']),
                    key=f"status_{order['id']}"
                )
                
                if new_status != order['status']:
                    update_order_status(order['id'], new_status)
                    st.success("Updated!")

st.markdown('<div class="fancy-divider"></div>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #999; margin-top: 40px;'>✨ Made with 💚 for organic wellness ✨</p>", unsafe_allow_html=True)
