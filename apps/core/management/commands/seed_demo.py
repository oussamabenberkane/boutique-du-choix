"""Commande de remplissage : seed_demo

Crée des catégories, produits (avec photos libres téléchargées), variantes,
avis et un compte administrateur de démonstration (admin / admin12345).

Usage :
    python manage.py seed_demo [--force]
"""

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageDraw

from apps.accounts.models import User
from apps.catalog.models import (
    Category,
    Product,
    ProductAttribute,
    ProductImage,
    ProductVariant,
    Review,
)


PEXELS_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)


def _placeholder(name, color, text="BDC", size=(800, 1000)):
    from io import BytesIO

    img = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, size[0] - 1, size[1] - 1], outline=(255, 255, 255), width=8)
    draw.rectangle([30, size[1] - 200, size[0] - 30, size[1] - 140], fill=(255, 255, 255))
    draw.text((46, size[1] - 191), text.upper(), fill=color)
    out = BytesIO()
    img.save(out, format="JPEG", quality=82)
    return ContentFile(out.getvalue())


def _fetch_stock_photo(url, color, text):
    """Télécharge une vraie photo libre (CDN Pexels).

    Retourne un ContentFile JPEG, ou laisse tomber sur un visuel local si
    le réseau est indisponible.
    """
    import urllib.error
    import urllib.request as urlreq

    try:
        req = urlreq.Request(url, headers={"User-Agent": PEXELS_UA})
        with urlreq.urlopen(req, timeout=20) as resp:
            if resp.status != 200:
                raise urllib.error.URLError(f"HTTP {resp.status}")
            data = resp.read(4 * 1024 * 1024)
    except (urllib.error.URLError, TimeoutError, OSError):
        return _placeholder("bdc", color, text=text)
    return ContentFile(data)


DEFS = [
    {
        "name": "Vêtements",
        "children": [
            {
                "name": "Pulls & Sweats",
                "products": [
                    {
                        "name": "Sweat à capuche premium",
                        "urls": [
                            "https://images.pexels.com/photos/9775536/pexels-photo-9775536.jpeg?auto=compress&cs=tinysrgb&w=900",
                            "https://images.pexels.com/photos/9775547/pexels-photo-9775547.jpeg?auto=compress&cs=tinysrgb&w=900",
                        ],
                        "price": 3900,
                        "compare": 5200,
                        "stock": 35,
                        "short": "Coton doux et épais, coupe moderne.",
                        "desc": "Un sweat ultra-confortable taillé dans un coton peigné 380 g/m². Capuche doublée, poche kangourou et finitions renforcées. Coupe légèrement oversize.\n\nLivré partout en Algérie.",
                        "attrs": [("Matière", "Coton peigné 380 g/m²"), ("Taille", "S – M – L – XL"), ("Entretien", "Lavage 30°")],
                        "variants": ["S — Gris", "M — Gris", "L — Gris", "XL — Noir"],
                        "featured": True,
                    },
                    {
                        "name": "Pull col rond basique",
                        "urls": [
                            "https://images.pexels.com/photos/10667736/pexels-photo-10667736.jpeg?auto=compress&cs=tinysrgb&w=900",
                            "https://images.pexels.com/photos/11000248/pexels-photo-11000248.jpeg?auto=compress&cs=tinysrgb&w=900",
                        ],
                        "price": 2400,
                        "compare": None,
                        "stock": 60,
                        "short": "L'intemporel à porter tous les jours.",
                        "desc": "Pull col rond en maille fine, doux au toucher. Idéal pour la mi-saison, se porte seul ou en superposition.\n\nDisponible en plusieurs coloris.",
                        "attrs": [("Matière", "Mélange coton/acrylique"), ("Taille", "S – M – L – XL")],
                        "variants": ["M — Beige", "L — Beige", "M — Marine"],
                    },
                ],
            },
            {
                "name": "T-shirts",
                "products": [
                    {
                        "name": "T-shirt col rond épais",
                        "urls": [
                            "https://images.pexels.com/photos/18186106/pexels-photo-18186106.jpeg?auto=compress&cs=tinysrgb&w=900",
                            "https://images.pexels.com/photos/12039633/pexels-photo-12039633.jpeg?auto=compress&cs=tinysrgb&w=900",
                        ],
                        "price": 1450,
                        "compare": 1800,
                        "stock": 120,
                        "short": "Coton épais, col renforcé, coupe droite.",
                        "desc": "T-shirt en coton compacté qui ne se déforme pas au lavage. Col rond renforcé et coutures planes pour un confort maximal.",
                        "attrs": [("Matière", "Coton 100%"), ("Taille", "S – M – L – XL")],
                        "variants": ["L — Blanc", "L — Noir", "M — Blanc"],
                    },
                    {
                        "name": "T-shirt manches courtes noir",
                        "urls": [
                            "https://images.pexels.com/photos/13134838/pexels-photo-13134838.jpeg?auto=compress&cs=tinysrgb&w=900",
                            "https://images.pexels.com/photos/18843501/pexels-photo-18843501.jpeg?auto=compress&cs=tinysrgb&w=900",
                        ],
                        "price": 1300,
                        "compare": None,
                        "stock": 0,
                        "short": "Le basique noir, indémodable.",
                        "desc": "Un t-shirt noir simple et efficace, lavable en machine sans effort.",
                        "attrs": [("Matière", "Coton bio"), ("Taille", "M – L")],
                    },
                ],
            },
        ],
    },
    {
        "name": "Chaussures",
        "children": [
            {
                "name": "Sneakers",
                "products": [
                    {
                        "name": "Sneakers blanches minimalistes",
                        "urls": [
                            "https://images.pexels.com/photos/4252969/pexels-photo-4252969.jpeg?auto=compress&cs=tinysrgb&w=900",
                            "https://images.pexels.com/photos/10726876/pexels-photo-10726876.jpeg?auto=compress&cs=tinysrgb&w=900",
                        ],
                        "price": 5200,
                        "compare": 6900,
                        "stock": 18,
                        "short": "Le style épuré qui va avec tout.",
                        "desc": "Sneakers blanches en cuir synthétique premium, semelle blanche crantée. Légères et confortables pour un usage quotidien.",
                        "attrs": [("Tige", "Cuir synthétique"), ("Pointures", "40 – 44"), ("Semelle", "EVA caoutchouc")],
                        "featured": True,
                    },
                    {
                        "name": "Baskets montantes noires",
                        "urls": [
                            "https://images.pexels.com/photos/12969390/pexels-photo-12969390.jpeg?auto=compress&cs=tinysrgb&w=900",
                            "https://images.pexels.com/photos/384553/pexels-photo-384553.jpeg?auto=compress&cs=tinysrgb&w=900",
                        ],
                        "price": 4900,
                        "compare": None,
                        "stock": 12,
                        "short": "Look streetwear assumé.",
                        "desc": "Baskets montantes noires, empeigne résistante et renforts cousus.",
                        "attrs": [("Tige", "Toile renforcée"), ("Pointures", "41 – 45")],
                    },
                ],
            },
        ],
    },
    {
        "name": "Accessoires",
        "children": [
            {
                "name": "Montres",
                "products": [
                    {
                        "name": "Montre bracelet acier inoxydable",
                        "urls": [
                            "https://images.pexels.com/photos/190819/pexels-photo-190819.jpeg?auto=compress&cs=tinysrgb&w=900",
                            "https://images.pexels.com/photos/1034063/pexels-photo-1034063.jpeg?auto=compress&cs=tinysrgb&w=900",
                        ],
                        "price": 3900,
                        "compare": 4800,
                        "stock": 25,
                        "short": "Minimaliste, étanche, pile de qualité.",
                        "desc": "Montre au cadran épuré montée sur bracelet acier. Étanche au quotidien, garantie 1 an.",
                        "attrs": [("Bracelet", "Acier inoxydable"), ("Étanchéité", "3 ATM"), ("Garantie", "1 an")],
                        "featured": True,
                    },
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Remplit la base avec des données de démonstration."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Recrée les données même si la base est remplie.")

    def handle(self, *args, **options):
        if options["force"]:
            self._clear_all()
        elif Product.objects.exists():
            self.stdout.write(self.style.WARNING("Des produits existent déjà ; utilisez --force pour recommencer."))
            return

        self._create_admin()
        palette = [
            (178, 103, 61), (31, 122, 61), (26, 78, 120),
            (120, 40, 60), (90, 90, 90), (200, 160, 90),
        ]
        color_index = 0
        count = 0
        for top_name, top_cfg in ((d["name"], d) for d in DEFS):
            top = Category.objects.create(name=top_name)
            for child_cfg in top_cfg["children"]:
                child = Category.objects.create(
                    name=child_cfg["name"], parent=top
                )
                for pdef in child_cfg["products"]:
                    color = palette[color_index % len(palette)]
                    color_index += 1
                    product = Product.objects.create(
                        category=child,
                        name=pdef["name"],
                        short_description=pdef["short"],
                        description=pdef["desc"],
                        price=pdef["price"],
                        compare_at_price=pdef["compare"],
                        stock=pdef["stock"],
                        is_featured=pdef.get("featured", False),
                    )
                    for idx, url in enumerate(pdef["urls"]):
                        file = _fetch_stock_photo(
                            url, color, text=product.name.split(" ")[0],
                        )
                        image = ProductImage(
                            product=product,
                            alt=f"{product.name} — photo {idx + 1}",
                            is_primary=(idx == 0),
                        )
                        image.image.save(
                            f"products/{product.pk}-{idx}.jpg", file, save=True
                        )
                    for label, value in pdef.get("attrs", []):
                        ProductAttribute.objects.create(
                            product=product, label=label, value=value
                        )
                    for vname in pdef.get("variants", []):
                        ProductVariant.objects.create(
                            product=product,
                            name=vname,
                            stock=max(3, pdef["stock"] // 2),
                        )
                    Review.objects.create(
                        product=product,
                        name="Client vérifié",
                        rating=5,
                        comment="Très bonne qualité, livraison rapide. Je recommande !",
                        is_approved=True,
                    )
                    count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Remplissage terminé : {count} produit(s), {len(DEFS)} rayons.")
        )

    def _create_admin(self):
        if User.objects.filter(username="admin").exists():
            return
        User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="admin12345",
            first_name="Admin",
        )
        self.stdout.write(
            self.style.SUCCESS("Compte admin créé : admin / admin12345 (à changer !)")
        )

    def _clear_all(self):
        Review.objects.all().delete()
        ProductImage.objects.all().delete()
        Variant = ProductVariant
        Variant.objects.all().delete()
        ProductAttribute.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        self.stdout.write(self.style.WARNING("Anciennes données supprimées."))