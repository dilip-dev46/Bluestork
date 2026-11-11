import io
import math

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# Approximate district headquarters (lat, lng) - used for pricing and the map.
DISTRICTS = {
    "Ariyalur": (11.14, 79.08), "Chengalpattu": (12.69, 79.98), "Chennai": (13.08, 80.27),
    "Coimbatore": (11.00, 76.96), "Cuddalore": (11.75, 79.77), "Dharmapuri": (12.13, 78.16),
    "Dindigul": (10.36, 77.98), "Erode": (11.34, 77.72), "Kallakurichi": (11.74, 78.96),
    "Kancheepuram": (12.83, 79.70), "Kanniyakumari": (8.18, 77.43), "Karur": (10.96, 78.08),
    "Krishnagiri": (12.52, 78.21), "Madurai": (9.92, 78.12), "Mayiladuthurai": (11.10, 79.65),
    "Nagapattinam": (10.77, 79.84), "Namakkal": (11.22, 78.17), "Nilgiris": (11.41, 76.70),
    "Perambalur": (11.23, 78.88), "Pudukkottai": (10.38, 78.82), "Ramanathapuram": (9.37, 78.83),
    "Ranipet": (12.93, 79.33), "Salem": (11.66, 78.15), "Sivaganga": (9.85, 78.48),
    "Tenkasi": (8.96, 77.31), "Thanjavur": (10.79, 79.14), "Theni": (10.01, 77.48),
    "Thoothukudi": (8.76, 78.13), "Tiruchirappalli": (10.79, 78.70), "Tirunelveli": (8.73, 77.70),
    "Tirupathur": (12.50, 78.57), "Tiruppur": (11.11, 77.34), "Tiruvallur": (13.14, 79.91),
    "Tiruvannamalai": (12.23, 79.07), "Tiruvarur": (10.77, 79.64), "Vellore": (12.92, 79.13),
    "Viluppuram": (11.94, 79.49), "Virudhunagar": (9.59, 77.96),
}
DISTRICT_CHOICES = [(d, d) for d in sorted(DISTRICTS)]

COMMISSION_RATE = 0.20  # Bluestork keeps 20%, partner gets 80%
MAX_WEIGHT_KG = 25


def distance_km(a, b):
    """Straight-line distance between two district centres x 1.1 (rough road factor)."""
    (lat1, lon1), (lat2, lon2) = DISTRICTS[a], DISTRICTS[b]
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return max(5, round(2 * 6371 * math.asin(math.sqrt(h)) * 1.1))


def quote(pickup, drop, weight_kg):
    """Returns (distance_km, customer_price, partner_payout) in rupees."""
    km = distance_km(pickup, drop)
    price = round(40 + 0.9 * km + 12 * float(weight_kg))
    payout = round(price * (1 - COMMISSION_RATE))
    return km, price, payout


# ---------------------------------------------------------------- PDF helpers
def _pdf(title, subtitle, rows, total_label, total, note):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    c.setFillColorRGB(0.09, 0.41, 0.89)
    c.rect(0, h - 90, w, 90, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(40, h - 52, "Bluestork")
    c.setFont("Helvetica", 11)
    c.drawString(40, h - 72, "Crowdshipping parcel delivery - Tamil Nadu")

    c.setFillColorRGB(0.06, 0.1, 0.18)
    c.setFont("Helvetica-Bold", 17)
    c.drawString(40, h - 130, title)
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.35, 0.4, 0.5)
    c.drawString(40, h - 146, subtitle)

    y = h - 185
    for label, value in rows:
        c.setFont("Helvetica", 10)
        c.setFillColorRGB(0.35, 0.4, 0.5)
        c.drawString(40, y, label)
        c.setFont("Helvetica-Bold", 10)
        c.setFillColorRGB(0.06, 0.1, 0.18)
        c.drawString(190, y, str(value)[:75])
        y -= 10
        c.setStrokeColorRGB(0.9, 0.92, 0.95)
        c.line(40, y, w - 40, y)
        y -= 14

    y -= 10
    c.setFillColorRGB(0.93, 0.96, 1)
    c.rect(40, y - 12, w - 80, 36, fill=1, stroke=0)
    c.setFillColorRGB(0.06, 0.1, 0.18)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(52, y, total_label)
    c.drawRightString(w - 52, y, total)

    c.setFont("Helvetica-Oblique", 9)
    c.setFillColorRGB(0.45, 0.5, 0.58)
    c.drawString(40, 50, note)
    c.showPage()
    c.save()
    return buf.getvalue()


def invoice_pdf(p):
    customer = p.customer.get_full_name() or p.customer.username
    rows = [
        ("Invoice no", f"INV-{p.code}"),
        ("Date", p.paid_at.astimezone().strftime("%d %b %Y, %I:%M %p")),
        ("Customer", customer),
        ("Parcel ID", p.code),
        ("Route", f"{p.pickup_district} to {p.drop_district} ({p.distance_km} km)"),
        ("Pickup address", p.pickup_address),
        ("Drop address", p.drop_address),
        ("Receiver", f"{p.receiver_name} ({p.receiver_phone})"),
        ("Weight / size", f"{p.weight_kg} kg / {p.get_size_display()}"),
        ("Contents", p.description),
        ("Payment method", f"{p.pay_method or 'Simulated'} (demo payment)"),
        ("Transaction ID", p.txn_id),
    ]
    return _pdf("Payment invoice", "Paid to Bluestork", rows, "Total paid", f"Rs. {p.price}",
                "Demo invoice generated from a simulated payment. No real money was charged.")


def payout_pdf(p):
    partner = p.partner.get_full_name() or p.partner.username
    commission = p.price - p.partner_payout
    rows = [
        ("Payout slip no", f"PAY-{p.code}"),
        ("Date", p.payout_at.astimezone().strftime("%d %b %Y, %I:%M %p")),
        ("Pickup partner", partner),
        ("Parcel ID", p.code),
        ("Route", f"{p.pickup_district} to {p.drop_district} ({p.distance_km} km)"),
        ("Delivered on", p.delivered_at.astimezone().strftime("%d %b %Y, %I:%M %p")),
        ("Parcel fare", f"Rs. {p.price}"),
        ("Bluestork commission", f"Rs. {commission}"),
        ("Payout reference", p.payout_ref),
    ]
    return _pdf("Partner payout slip", "Paid by Bluestork", rows, "Amount paid to partner",
                f"Rs. {p.partner_payout}", "Demo payout slip generated from a simulated payout.")
