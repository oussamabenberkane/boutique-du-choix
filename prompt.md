**Project: Minimalist Django E-Commerce Platform**

Build a Django-based e-commerce web application with the following requirements:

**Core Functionality**
- Product catalog with categories, variants (size/color if applicable), pricing, stock tracking, and images (multiple per product)
- Cart and checkout flow (guest checkout should work; account creation optional, not required)
- Order management (order history, status tracking: pending/paid/shipped/delivered/cancelled)
- Payment integration — ask me which provider(s) I want before implementing (e.g. Stripe, PayPal, or a local payment gateway) if I haven't specified one
- Search and filtering (by category, price range, availability)

**Automatic Landing Pages**
- Every product should automatically get its own dedicated landing page at a clean URL (e.g. `/products/<slug>/`) — no manual page-building required per product
- Each landing page should be generated from the product's data (title, description, images, price, specs, reviews if applicable) using a consistent, reusable template
- Support rich product descriptions (structured fields, not just a single text blob) so landing pages look complete even for products with minimal admin input

**Admin Panel**
- Use Django's built-in admin as the base, but customize it to be genuinely easy for a non-technical person to use:
  - Clear, minimal forms for adding/editing products (drag-and-drop image upload if feasible)
  - Inline editing for variants/stock
  - Bulk actions (bulk price update, bulk activate/deactivate)
  - Dashboard view with basic sales/inventory overview
- Ask me before adding any admin functionality beyond product/order/inventory management (e.g. discounts, coupons, analytics) — don't assume scope

**Styling / Design Direction**
- Minimalist aesthetic, but the priority is **conversion and marketability**, not just "clean" for its own sake — think high-converting DTC e-commerce sites (e.g. Shopify's better-designed stores), not a bare-bones template
- Strong typography, generous whitespace, clear visual hierarchy, prominent CTAs (Add to Cart / Buy Now), trust signals (reviews, guarantees, shipping info) placed where they support conversion
- Fully responsive/mobile-first, since most e-commerce traffic is mobile
- Fast page loads — optimize images, avoid heavy unnecessary JS

**Technical Expectations**
- Django + Django REST Framework if an API layer is needed (ask me if this should be server-rendered templates, a separate frontend, or both)
- PostgreSQL for the database
- Reasonable test coverage for cart/checkout/order logic
- Clear project structure (separate apps: products, orders, cart, accounts, etc.)

**Process**
- Before writing code, ask me clarifying questions on anything ambiguous — especially: payment provider, whether I want a separate frontend (React/Next) vs Django templates, hosting target, whether multi-currency/multi-language is needed, and what "product" fields I actually need for my catalog
- Propose your planned app structure and models before implementing, so I can review before you build