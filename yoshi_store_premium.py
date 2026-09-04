import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
import io
from datetime import datetime

# ═════════════════════════════════════════════════════════════════════════════
# DATABASE SETUP
# ═════════════════════════════════════════════════════════════════════════════

DB_FILE = "oishi_premium.db"

def init_db():
    """Initialize database - NO DEFAULT DATA"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Brand Settings
    c.execute('''
        CREATE TABLE IF NOT EXISTS brand_settings (
            id INTEGER PRIMARY KEY,
            brand_name TEXT DEFAULT 'OISHI',
            tagline TEXT DEFAULT 'Purely Herbal, Purely Divine',
            primary_color TEXT DEFAULT '#2d5016',
            secondary_color TEXT DEFAULT '#d4af37',
            accent_color TEXT DEFAULT '#f5f0e8',
            logo_emoji TEXT DEFAULT '🌿',
            about_text TEXT
        )
    ''')
    
    # Categories Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            emoji TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Products Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            name TEXT NOT NULL,
            description TEXT,
            ingredients TEXT,
            benefits TEXT,
            price REAL NOT NULL,
            discount_price REAL,
            rating REAL DEFAULT 5.0,
            reviews INTEGER DEFAULT 0,
            image_data BLOB,
            badge TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
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
            INSERT INTO brand_settings (brand_name, tagline, logo_emoji, about_text)
            VALUES (?, ?, ?, ?)
        ''', ('OISHI', 'Purely Herbal, Purely Divine', '🌿', 
              'Welcome to OISHI - where ancient herbal wisdom meets modern wellness. Every product is crafted with pure, organic ingredients.'))
    
    conn.commit()
    conn.close()

init_db()

# ═════════════════════════════════════════════════════════════════════════════
# DATABASE FUNCTIONS
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
            'accent_color': row[5],
            'logo_emoji': row[6],
            'about_text': row[7]
        }
    return {}

def update_brand_settings(brand_name, tagline, primary_color, secondary_color, accent_color, logo_emoji, about_text):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        UPDATE brand_settings 
        SET brand_name=?, tagline=?, primary_color=?, secondary_color=?, accent_color=?, logo_emoji=?, about_text=?
        WHERE id = 1
    ''', (brand_name, tagline, primary_color, secondary_color, accent_color, logo_emoji, about_text))
    conn.commit()
    conn.close()

def get_categories():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT id, name, emoji, description FROM categories ORDER BY created_at DESC", conn)
    conn.close()
    return df

def add_category(name, emoji, description):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO categories (name, emoji, description) VALUES (?, ?, ?)", (name, emoji, description))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def update_category(cat_id, name, emoji, description):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE categories SET name=?, emoji=?, description=? WHERE id=?", (name, emoji, description, cat_id))
    conn.commit()
    conn.close()

def delete_category(cat_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE category_id=?", (cat_id,))
    c.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    conn.commit()
    conn.close()

def get_products(category_id=None, search_query=None):
    conn = sqlite3.connect(DB_FILE)
    query = '''
        SELECT p.id, p.category_id, p.name, p.description, p.ingredients, p.benefits, 
               p.price, p.discount_price, p.rating, p.reviews, p.image_data, p.badge,
               c.name as category_name, c.emoji as category_emoji
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE 1=1
    '''
    params = []
    
    if category_id:
        query += " AND p.category_id = ?"
        params.append(category_id)
    if search_query:
        query += " AND (p.name LIKE ? OR p.ingredients LIKE ? OR p.benefits LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"])
    
    query += " ORDER BY p.created_at DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def add_product(category_id, name, description, ingredients, benefits, price, discount_price, badge, image_data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO products (category_id, name, description, ingredients, benefits, price, discount_price, badge, image_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (category_id, name, description, ingredients, benefits, price, discount_price, badge, image_data))
    conn.commit()
    conn.close()

def update_product(prod_id, name, description, ingredients, benefits, price, discount_price, badge, image_data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if image_data:
        c.execute('''
            UPDATE products 
            SET name=?, description=?, ingredients=?, benefits=?, price=?, discount_price=?, badge=?, image_data=?
            WHERE id=?
        ''', (name, description, ingredients, benefits, price, discount_price, badge, image_data, prod_id))
    else:
        c.execute('''
            UPDATE products 
            SET name=?, description=?, ingredients=?, benefits=?, price=?, discount_price=?, badge=?
            WHERE id=?
        ''', (name, description, ingredients, benefits, price, discount_price, badge, prod_id))
    conn.commit()
    conn.close()

def delete_product(prod_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id=?", (prod_id,))
    conn.commit()
    conn.close()

def save_order(name, email, phone, address, city, pincode, items_summary, total_amount, payment_method):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO orders (customer_name, customer_email, customer_phone, address, city, pincode, items_summary, total_amount, payment_method, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, email, phone, address, city, pincode, items_summary, total_amount, payment_method, "Confirmed ✅"))
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
    page_title="OISHI - Purely Herbal",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

brand = get_brand_settings()

# ═════════════════════════════════════════════════════════════════════════════
# PREMIUM CSS - OPTIMIZED DESIGN
# ═════════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<style>
    :root {{
        --primary: {brand['primary_color']};
        --secondary: {brand['secondary_color']};
        --accent: {brand['accent_color']};
        --text-dark: #1a1a1a;
        --text-light: #666666;
        --border: #e5e5e5;
        --success: #27ae60;
    }}
    
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    
    html, body {{
        background-color: #ffffff;
        color: var(--text-dark);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
        line-height: 1.6;
    }}
    
    /* ===== TYPOGRAPHY ===== */
    h1 {{ font-size: 3rem; font-weight: 800; color: var(--primary); letter-spacing: -1px; margin-bottom: 10px; }}
    h2 {{ font-size: 2rem; font-weight: 700; color: var(--primary); margin: 30px 0 15px 0; }}
    h3 {{ font-size: 1.4rem; font-weight: 600; color: var(--primary); margin: 20px 0 10px 0; }}
    h4 {{ font-size: 1.1rem; font-weight: 600; color: var(--text-dark); }}
    p {{ color: var(--text-light); line-height: 1.8; }}
    
    /* ===== HERO SECTION ===== */
    .hero {{
        background: linear-gradient(135deg, var(--primary) 0%, #1f3a0f 100%);
        color: white;
        padding: 80px 40px;
        border-radius: 0;
        text-align: center;
        margin-bottom: 60px;
        box-shadow: 0 10px 40px rgba(45, 80, 22, 0.15);
        position: relative;
        overflow: hidden;
    }}
    
    .hero::before {{
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        border-radius: 50%;
    }}
    
    .hero-content {{
        position: relative;
        z-index: 2;
    }}
    
    .hero-logo {{
        font-size: 4.5rem;
        margin-bottom: 20px;
        text-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }}
    
    .hero-title {{
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 10px;
        letter-spacing: -1px;
    }}
    
    .hero-tagline {{
        font-size: 1.4rem;
        font-weight: 300;
        color: rgba(255, 255, 255, 0.95);
        margin-bottom: 0;
    }}
    
    /* ===== CATEGORY PILLS ===== */
    .category-container {{
        display: flex;
        gap: 15px;
        overflow-x: auto;
        padding: 30px 0;
        margin-bottom: 40px;
        justify-content: center;
        flex-wrap: wrap;
    }}
    
    .category-pill {{
        background: white;
        border: 2px solid var(--border);
        color: var(--text-dark);
        padding: 12px 24px;
        border-radius: 50px;
        cursor: pointer;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.3s ease;
        white-space: nowrap;
    }}
    
    .category-pill:hover {{
        border-color: var(--primary);
        background: var(--accent);
        color: var(--primary);
        transform: translateY(-3px);
        box-shadow: 0 5px 15px rgba(45, 80, 22, 0.1);
    }}
    
    .category-pill.active {{
        background: var(--primary);
        color: white;
        border-color: var(--primary);
    }}
    
    /* ===== SEARCH BAR ===== */
    .search-container {{
        margin-bottom: 50px;
        display: flex;
        justify-content: center;
        gap: 15px;
    }}
    
    .search-box {{
        background: white;
        border: 2px solid var(--border);
        border-radius: 50px;
        padding: 15px 25px;
        width: 100%;
        max-width: 500px;
        font-size: 1rem;
        transition: all 0.3s ease;
    }}
    
    .search-box:focus {{
        outline: none;
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(45, 80, 22, 0.1);
    }}
    
    /* ===== PRODUCT GRID ===== */
    .products-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 35px;
        margin-bottom: 60px;
    }}
    
    /* ===== PRODUCT CARD - PREMIUM DESIGN ===== */
    .product-card {{
        background: white;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid var(--border);
        display: flex;
        flex-direction: column;
        height: 100%;
    }}
    
    .product-card:hover {{
        transform: translateY(-12px);
        box-shadow: 0 15px 40px rgba(45, 80, 22, 0.15);
        border-color: var(--primary);
    }}
    
    .product-image {{
        width: 100%;
        height: 280px;
        background: linear-gradient(135deg, #f5f0e8 0%, #ede8e0 100%);
        overflow: hidden;
        position: relative;
    }}
    
    .product-image img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.4s ease;
    }}
    
    .product-card:hover .product-image img {{
        transform: scale(1.05);
    }}
    
    .product-badge {{
        position: absolute;
        top: 15px;
        right: 15px;
        background: linear-gradient(135deg, var(--secondary) 0%, #d4a537 100%);
        color: var(--primary);
        padding: 8px 16px;
        border-radius: 50px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 4px 12px rgba(212, 175, 55, 0.25);
    }}
    
    .product-content {{
        padding: 25px;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
    }}
    
    .product-name {{
        font-size: 1.15rem;
        font-weight: 700;
        color: var(--text-dark);
        margin-bottom: 8px;
        line-height: 1.4;
    }}
    
    .product-ingredients {{
        font-size: 0.85rem;
        color: var(--text-light);
        margin-bottom: 12px;
        font-style: italic;
    }}
    
    .product-rating {{
        font-size: 0.9rem;
        color: var(--text-light);
        margin-bottom: 15px;
    }}
    
    .product-benefits {{
        font-size: 0.9rem;
        color: var(--text-light);
        margin-bottom: 15px;
        flex-grow: 1;
        line-height: 1.6;
    }}
    
    .product-price {{
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
        padding-top: 15px;
        border-top: 1px solid var(--border);
    }}
    
    .price-original {{
        text-decoration: line-through;
        color: var(--text-light);
        font-size: 0.95rem;
    }}
    
    .price-current {{
        font-size: 1.6rem;
        font-weight: 800;
        color: var(--primary);
    }}
    
    .discount-tag {{
        background: #fff3cd;
        color: #b8860b;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }}
    
    /* ===== BUTTONS ===== */
    .stButton>button {{
        background: linear-gradient(135deg, var(--primary) 0%, #1f3a0f 100%);
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 28px !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(45, 80, 22, 0.2) !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        width: 100%;
    }}
    
    .stButton>button:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(45, 80, 22, 0.35) !important;
    }}
    
    /* ===== EMPTY STATE ===== */
    .empty-state {{
        text-align: center;
        padding: 80px 40px;
        background: var(--accent);
        border-radius: 16px;
        border: 2px dashed var(--border);
    }}
    
    .empty-state-icon {{
        font-size: 4rem;
        margin-bottom: 20px;
    }}
    
    .empty-state h3 {{
        margin-bottom: 10px;
    }}
    
    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, var(--primary) 0%, #1f3a0f 100%);
    }}
    
    /* ===== DIVIDER ===== */
    .divider {{
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, var(--primary) 50%, transparent 100%);
        margin: 40px 0;
        border-radius: 1px;
    }}
    
    /* ===== FORMS ===== */
    .stTextInput>div>div>input,
    .stSelectbox>div>div>select,
    .stTextArea>div>div>textarea {{
        border-radius: 8px !important;
        border: 1px solid var(--border) !important;
        padding: 12px !important;
    }}
    
    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 20px;
        border-bottom: 2px solid var(--border) !important;
    }}
    
    .stTabs [role="tab"] {{
        font-weight: 600;
        color: var(--text-light);
        border: none !important;
        border-bottom: 3px solid transparent !important;
        padding: 15px 0 !important;
    }}
    
    .stTabs [role="tab"][aria-selected="true"] {{
        color: var(--primary) !important;
        border-bottom: 3px solid var(--primary) !important;
    }}
    
    /* ===== NO PADDING ===== */
    .block-container {{
        padding-left: 2rem;
        padding-right: 2rem;
    }}
    
    /* ===== METRICS ===== */
    .metric {{
        background: var(--accent);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid var(--border);
    }}
</style>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═════════════════════════════════════════════════════════════════════════════

if "cart" not in st.session_state:
    st.session_state.cart = {}

# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ═════════════════════════════════════════════════════════════════════════════

st.sidebar.markdown(f"""
<div style="text-align: center; padding: 20px 0; border-bottom: 2px solid rgba(255,255,255,0.1); margin-bottom: 20px;">
    <div style="font-size: 3rem; margin-bottom: 10px;">{brand['logo_emoji']}</div>
    <h2 style="color: white; margin: 0; font-size: 1.3rem;">{brand['brand_name']}</h2>
    <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0 0; font-size: 0.9rem;">{brand['tagline']}</p>
</div>
""", unsafe_allow_html=True)

pages = {
    "🛍️ Shop": "shop",
    "🛒 Cart": "cart",
    "📦 Orders": "orders",
    "ℹ️ About": "about",
    "⚙️ Admin": "admin"
}

selected_page = st.sidebar.radio("Navigate:", list(pages.keys()), label_visibility="collapsed")
current_page = pages[selected_page]

cart_count = sum(item["qty"] for item in st.session_state.cart.values())
st.sidebar.markdown("---")
if cart_count > 0:
    st.sidebar.metric("🛒 Cart Items", cart_count)
else:
    st.sidebar.markdown("<p style='text-align: center; color: #999;'>🛒 Cart Empty</p>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: SHOP
# ═════════════════════════════════════════════════════════════════════════════

if current_page == "shop":
    # HERO SECTION
    st.markdown(f"""
    <div class="hero">
        <div class="hero-content">
            <div class="hero-logo">{brand['logo_emoji']}</div>
            <div class="hero-title">{brand['brand_name']}</div>
            <div class="hero-tagline">{brand['tagline']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # GET CATEGORIES
    categories_df = get_categories()
    
    if categories_df.empty:
        # EMPTY STATE
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📂</div>
            <h3>No Categories Yet</h3>
            <p>Visit the Admin section to create categories and add your first products!</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # CATEGORY FILTER
        col_cats = st.columns([10, 1])
        
        with col_cats[0]:
            st.markdown("### Explore Our Collections")
            cat_list = ["All Products"] + categories_df['name'].tolist()
            
            st.markdown('<div class="category-container">', unsafe_allow_html=True)
            
            cat_col = st.columns(len(cat_list))
            selected_category = None
            
            for idx, cat in enumerate(cat_list):
                with cat_col[idx]:
                    if st.button(cat, key=f"cat_{idx}", use_container_width=True):
                        st.session_state.selected_cat = cat
            
            if "selected_cat" in st.session_state:
                selected_category = st.session_state.selected_cat
            else:
                selected_category = "All Products"
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # SEARCH BAR
        st.markdown('<div class="search-container">', unsafe_allow_html=True)
        search_term = st.text_input("🔍 Search products", placeholder="Search by name, ingredients, benefits...", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # GET PRODUCTS
        category_id = None
        if selected_category != "All Products":
            category_id = categories_df[categories_df['name'] == selected_category]['id'].values[0]
        
        products_df = get_products(category_id=category_id, search_query=search_term if search_term else None)
        
        # DISPLAY PRODUCTS
        if products_df.empty:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">🌿</div>
                <h3>No Products Found</h3>
                <p>Try adjusting your search or browse other categories.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # PRODUCT GRID
            st.markdown('<div class="products-grid">', unsafe_allow_html=True)
            
            for idx, (_, product) in enumerate(products_df.iterrows()):
                col = st.columns(3)[(idx % 3)]
                
                with col:
                    # PRODUCT CARD
                    st.markdown('<div class="product-card">', unsafe_allow_html=True)
                    
                    # IMAGE
                    st.markdown('<div class="product-image">', unsafe_allow_html=True)
                    if product['image_data']:
                        try:
                            img = Image.open(io.BytesIO(product['image_data']))
                            st.image(img, use_container_width=True)
                        except:
                            st.image("https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=500&auto=format&fit=crop&q=60", use_container_width=True)
                    else:
                        st.image("https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=500&auto=format&fit=crop&q=60", use_container_width=True)
                    
                    # BADGE
                    if product['badge']:
                        st.markdown(f'<span class="product-badge">{product["badge"]}</span>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # CONTENT
                    st.markdown('<div class="product-content">', unsafe_allow_html=True)
                    
                    st.markdown(f'<div class="product-name">{product["name"]}</div>', unsafe_allow_html=True)
                    
                    if product['ingredients']:
                        st.markdown(f'<div class="product-ingredients">🌿 {product["ingredients"]}</div>', unsafe_allow_html=True)
                    
                    st.markdown(f'<div class="product-rating">⭐ {product["rating"]} ({int(product["reviews"])} reviews)</div>', unsafe_allow_html=True)
                    
                    if product['benefits']:
                        st.markdown(f'<div class="product-benefits">{product["benefits"]}</div>', unsafe_allow_html=True)
                    
                    # PRICING
                    discount = 0
                    if product['discount_price'] and product['price'] > product['discount_price']:
                        discount = int(((product['price'] - product['discount_price']) / product['price']) * 100)
                    
                    st.markdown(f"""
                    <div class="product-price">
                        <span class="price-original">₹{int(product['price'])}</span>
                        <span class="price-current">₹{int(product['discount_price']) if product['discount_price'] else int(product['price'])}</span>
                        {f'<span class="discount-tag">{discount}% OFF</span>' if discount > 0 else ''}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # ADD TO CART
                    if st.button(f"🛒 Add to Cart", key=f"add_{product['id']}", use_container_width=True):
                        pid = str(product['id'])
                        if pid in st.session_state.cart:
                            st.session_state.cart[pid]["qty"] += 1
                        else:
                            st.session_state.cart[pid] = {
                                "name": product['name'],
                                "price": product['discount_price'] if product['discount_price'] else product['price'],
                                "qty": 1
                            }
                        st.success(f"✅ Added to cart!")
                        st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: CART & CHECKOUT
# ═════════════════════════════════════════════════════════════════════════════

elif current_page == "cart":
    st.markdown("## 🛒 Shopping Cart")
    
    if not st.session_state.cart:
        st.info("Your cart is empty. Let's add some amazing products! ✨")
    else:
        # CART ITEMS
        cart_items = []
        subtotal = 0
        
        for pid, item in list(st.session_state.cart.items()):
            item_total = item['price'] * item['qty']
            subtotal += item_total
            cart_items.append({
                "Product": item['name'],
                "Price": f"₹{int(item['price'])}",
                "Qty": item['qty'],
                "Total": f"₹{int(item_total)}",
                "pid": pid
            })
        
        cart_df = pd.DataFrame(cart_items)
        st.dataframe(cart_df[["Product", "Price", "Qty", "Total"]], use_container_width=True, hide_index=True)
        
        # CART ACTIONS
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Cart", use_container_width=True):
                st.session_state.cart = {}
                st.success("Cart cleared!")
                st.rerun()
        with col2:
            if st.button("← Continue Shopping", use_container_width=True):
                st.switch_page("pages/shop.py") if False else None
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # PRICING
        shipping = 0 if subtotal >= 399 else 49
        total = subtotal + shipping
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Subtotal", f"₹{int(subtotal)}")
        col2.metric("Shipping", f"₹{int(shipping)}")
        col3.metric("Total", f"₹{int(total)}")
        
        if shipping > 0:
            st.info(f"💡 Add ₹{int(399 - subtotal)} more for FREE Delivery!")
        else:
            st.success("🎉 FREE Delivery Qualified!")
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # CHECKOUT FORM
        st.markdown("### 📦 Delivery & Payment")
        with st.form("checkout_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name *")
                email = st.text_input("Email *")
            with col2:
                phone = st.text_input("Phone *")
                city = st.text_input("City *")
            
            address = st.text_area("Address *", height=80)
            pincode = st.text_input("Pincode *")
            payment = st.selectbox("Payment Method", ["💳 Card", "📱 UPI", "💵 Cash on Delivery"])
            
            if st.form_submit_button("🚀 Place Order", use_container_width=True):
                if all([name, email, phone, address, city, pincode]):
                    items_str = ", ".join([f"{item['name']} (x{item['qty']})" for item in st.session_state.cart.values()])
                    order_id = save_order(name, email, phone, address, city, pincode, items_str, total, payment)
                    st.balloons()
                    st.success(f"✅ Order Confirmed! Order ID: #OISHI-{order_id:04d}")
                    st.session_state.cart = {}
                else:
                    st.error("Please fill all required fields!")

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: ORDERS
# ═════════════════════════════════════════════════════════════════════════════

elif current_page == "orders":
    st.markdown("## 📦 Your Orders")
    
    orders_df = get_orders()
    
    if orders_df.empty:
        st.info("No orders yet. Start shopping!")
    else:
        for _, order in orders_df.iterrows():
            with st.expander(f"Order #OISHI-{order['id']:04d} - {order['order_date'][:10]}", expanded=False):
                col1, col2, col3 = st.columns(3)
                col1.markdown(f"**Status:** {order['status']}")
                col2.markdown(f"**Amount:** ₹{int(order['total_amount'])}")
                col3.markdown(f"**Payment:** {order['payment_method']}")
                
                st.markdown(f"""
                **Items:** {order['items_summary']}
                
                **Address:** {order['address']}, {order['city']} - {order['pincode']}
                
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
        ## About {brand['brand_name']}
        
        {brand['about_text']}
        
        ### Our Promise
        - 🌿 100% Pure & Organic
        - 🧪 No Harmful Chemicals
        - ⭐ Premium Quality
        - 💚 Sustainable
        """)

# ═════════════════════════════════════════════════════════════════════════════
# PAGE: ADMIN
# ═════════════════════════════════════════════════════════════════════════════

elif current_page == "admin":
    st.markdown("## ⚙️ Admin Dashboard")
    
    admin_tabs = st.tabs(["🎨 Branding", "📂 Categories", "🛍️ Products", "📦 Orders"])
    
    # TAB 1: BRANDING
    with admin_tabs[0]:
        st.markdown("### Customize Your Brand")
        with st.form("brand_form"):
            col1, col2 = st.columns(2)
            with col1:
                brand_name = st.text_input("Brand Name", value=brand['brand_name'])
                tagline = st.text_input("Tagline", value=brand['tagline'])
                logo_emoji = st.text_input("Logo Emoji", value=brand['logo_emoji'])
                primary_color = st.color_picker("Primary Color", value=brand['primary_color'])
            with col2:
                secondary_color = st.color_picker("Secondary Color", value=brand['secondary_color'])
                accent_color = st.color_picker("Accent Color", value=brand['accent_color'])
                about_text = st.text_area("About Text", value=brand['about_text'], height=100)
            
            if st.form_submit_button("💾 Save Settings"):
                update_brand_settings(brand_name, tagline, primary_color, secondary_color, accent_color, logo_emoji, about_text)
                st.success("✅ Brand updated!")
                st.rerun()
    
    # TAB 2: CATEGORIES
    with admin_tabs[1]:
        st.markdown("### Manage Categories")
        
        subtab1, subtab2, subtab3 = st.tabs(["View", "Add", "Edit/Delete"])
        
        with subtab1:
            cats = get_categories()
            if cats.empty:
                st.info("No categories yet. Create one!")
            else:
                st.dataframe(cats, use_container_width=True, hide_index=True)
        
        with subtab2:
            with st.form("add_cat_form"):
                cat_name = st.text_input("Category Name *")
                cat_emoji = st.text_input("Emoji", value="🌿")
                cat_desc = st.text_input("Description")
                
                if st.form_submit_button("Add Category"):
                    if cat_name:
                        if add_category(cat_name, cat_emoji, cat_desc):
                            st.success(f"✅ Added '{cat_name}'!")
                            st.rerun()
                        else:
                            st.error("Category already exists!")
        
        with subtab2:
            cats = get_categories()
            if not cats.empty:
                st.markdown("### Edit or Delete Categories")
                for _, cat in cats.iterrows():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.write(f"{cat['emoji']} {cat['name']}")
                    
                    if col2.button("✏️", key=f"edit_{cat['id']}", use_container_width=True):
                        with st.form(f"edit_cat_{cat['id']}"):
                            new_name = st.text_input("Name", value=cat['name'])
                            new_emoji = st.text_input("Emoji", value=cat['emoji'])
                            new_desc = st.text_input("Description", value=cat['description'] or "")
                            
                            if st.form_submit_button("Update"):
                                update_category(cat['id'], new_name, new_emoji, new_desc)
                                st.success("✅ Updated!")
                                st.rerun()
                    
                    if col3.button("🗑️", key=f"del_{cat['id']}", use_container_width=True):
                        delete_category(cat['id'])
                        st.success("✅ Deleted!")
                        st.rerun()
    
    # TAB 3: PRODUCTS
    with admin_tabs[2]:
        st.markdown("### Manage Products")
        
        ptabs = st.tabs(["View", "Add", "Edit"])
        
        with ptabs[0]:
            prods = get_products()
            if prods.empty:
                st.info("No products yet!")
            else:
                st.dataframe(prods[['name', 'category_name', 'price', 'discount_price', 'badge']], use_container_width=True, hide_index=True)
        
        with ptabs[1]:
            with st.form("add_prod_form"):
                cats = get_categories()
                
                if cats.empty:
                    st.error("Please create a category first!")
                else:
                    cat_name = st.selectbox("Category *", cats['name'].tolist())
                    cat_id = cats[cats['name'] == cat_name]['id'].values[0]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        prod_name = st.text_input("Product Name *")
                        prod_price = st.number_input("Price ₹", min_value=1.0, value=299.0)
                        prod_badge = st.text_input("Badge (e.g., Best Seller ⭐)")
                    with col2:
                        prod_disc = st.number_input("Discount Price ₹", min_value=0.0, value=0.0)
                        prod_rating = st.number_input("Rating", min_value=0.0, max_value=5.0, value=5.0)
                        prod_reviews = st.number_input("Reviews", min_value=0, value=0)
                    
                    prod_desc = st.text_area("Description")
                    prod_ingr = st.text_input("Ingredients")
                    prod_ben = st.text_area("Benefits")
                    prod_img = st.file_uploader("Product Image", type=["jpg", "jpeg", "png", "webp"])
                    
                    if st.form_submit_button("Add Product"):
                        if prod_name:
                            img_bytes = prod_img.read() if prod_img else None
                            add_product(cat_id, prod_name, prod_desc, prod_ingr, prod_ben, prod_price, prod_disc if prod_disc > 0 else None, prod_badge, img_bytes)
                            st.success(f"✅ Added '{prod_name}'!")
                            st.rerun()
        
        with ptabs[2]:
            prods = get_products()
            if not prods.empty:
                selected_prod = st.selectbox("Select Product", prods['name'].tolist())
                prod_data = prods[prods['name'] == selected_prod].iloc[0]
                
                with st.form("edit_prod_form"):
                    prod_name = st.text_input("Name", value=prod_data['name'])
                    prod_price = st.number_input("Price", value=float(prod_data['price']))
                    prod_disc = st.number_input("Discount Price", value=float(prod_data['discount_price']) if prod_data['discount_price'] else 0.0)
                    prod_badge = st.text_input("Badge", value=prod_data['badge'] or "")
                    prod_desc = st.text_area("Description", value=prod_data['description'] or "")
                    prod_ingr = st.text_input("Ingredients", value=prod_data['ingredients'] or "")
                    prod_ben = st.text_area("Benefits", value=prod_data['benefits'] or "")
                    prod_img = st.file_uploader("New Image (optional)", type=["jpg", "jpeg", "png", "webp"])
                    
                    if st.form_submit_button("Update Product"):
                        img_bytes = prod_img.read() if prod_img else None
                        update_product(prod_data['id'], prod_name, prod_desc, prod_ingr, prod_ben, prod_price, prod_disc if prod_disc > 0 else None, prod_badge, img_bytes)
                        st.success("✅ Updated!")
                        st.rerun()
    
    # TAB 4: ORDERS
    with admin_tabs[3]:
        st.markdown("### Manage Orders")
        orders_df = get_orders()
        
        if orders_df.empty:
            st.info("No orders yet!")
        else:
            for _, order in orders_df.iterrows():
                col1, col2 = st.columns([4, 1])
                col1.write(f"**Order #OISHI-{order['id']:04d}** - {order['customer_name']} - ₹{int(order['total_amount'])}")
                
                new_status = col2.selectbox(
                    "Status",
                    ["Confirmed ✅", "Processing 🔄", "Shipped 🚚", "Delivered 📦"],
                    index=["Confirmed ✅", "Processing 🔄", "Shipped 🚚", "Delivered 📦"].index(order['status']),
                    key=f"status_{order['id']}"
                )
                
                if new_status != order['status']:
                    update_order_status(order['id'], new_status)
                    st.success("Updated!")
                    st.rerun()

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #999; padding: 20px 0;'>✨ OISHI - Purely Herbal, Purely Divine ✨</p>", unsafe_allow_html=True)
