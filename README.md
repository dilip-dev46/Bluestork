# Bluestork - crowdshipping parcel delivery (Tamil Nadu, inter-district)

Django app, mobile-first (works on phone and PC). **All payments are simulated.**

## Run it
```bash
python -m venv venv
venv\Scripts\activate          # Windows   (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser     # this is your Django admin login
python manage.py runserver 0.0.0.0:8000
```
Open http://127.0.0.1:8000 on your PC.
On your phone (same Wi-Fi): http://YOUR-PC-IP:8000  (find the IP with `ipconfig` / `ifconfig`).

## Menu (3-line button, top left)
Customer - Pickup Partner - Assigner - Settings & theme - Admin (Django). Log out appears when logged in.
Customer, Partner and Assigner each go to their own ID + password login.

## Accounts
* **Customer / Pickup partner**: sign up from their login page.
* **Assigner**: NO sign-up. Create it in Django admin:
  `/admin/` -> Users -> Add user -> set username + password -> in the *Profile* section choose
  **Role = Parcel Assigner** -> Save.

## Flow
1. Customer creates a parcel (fare is estimated live) and pays Bluestork (simulated) -> downloads **invoice PDF**.
2. Assigner board lists paid parcels; partners are sorted by route match (exact / reverse / partial) and capacity.
3. Partner accepts or rejects. Pickup OTP (from customer) -> in transit. Delivery OTP (from receiver) -> delivered.
4. Assigner pays the partner's share (simulated) -> partner downloads **payout slip PDF**.

Pricing (core/utils.py): Rs.40 + Rs.0.9/km + Rs.12/kg. Bluestork keeps 20%, partner gets 80%.

## Live map
Leaflet + OpenStreetMap (internet needed for map tiles). The partner can share real GPS or use
"Simulate trip (demo)". Phones only allow real GPS on HTTPS/localhost, so use the demo button on plain Wi-Fi testing.

## Themes
Settings page: Light, Dark, Ocean (saved on the device).

## Not built yet (next steps)
KYC document upload and approval, real SMS OTP login, Razorpay, disputes and ratings, native Android app.
