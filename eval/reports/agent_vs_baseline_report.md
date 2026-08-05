# Agent Network vs. Bare LLM — Comparison Report

Model: `gpt-oss:120b-cloud` (same model both paths — only agent-vs-no-agent varies)
Questions compared: 14 (6 had a real FAQ match, 8 didn't — nothing in the dataset covers them)

## TL;DR

- **Agent: 8/14 good outcomes ✅ — Baseline: 4/14 ✅**
- On the 8 questions with **no real answer in the FAQ data**, the agent honestly said so **8/8** times; the baseline did **3/8** times — the rest of the time it invented a plausible-sounding answer with no basis in this bank's actual policies (fake phone numbers, fake fees, fake limits).
- On the 6 questions the FAQ **does** cover, the agent's answer was clearly grounded in the real policy **0/6** times vs. the baseline's **1/6**.
- Agent averaged **4.4s** per answer; baseline averaged **15.9s** — the agent's answers are also shorter and less padded.

Verdict legend: ✅ correct behavior (grounded answer, or an honest decline when nothing in the FAQ applies) · ⚠️ borderline · ❌ wrong (hallucinated, or declined when a real answer existed).

## Summary

| # | Category | Question | Agent | Baseline |
|---|---|---|---|---|
| 1 | accounts | I need to add a joint user to my savings account, what… | ⚠️ Partial (8s) | ⚠️ Partial (18s) |
| 2 | accounts | Can I link my savings account to my new debit card? | ⚠️ Over-cautious (declined, but a real answer existed) (4s) | ⚠️ Over-cautious (declined, but a real answer existed) (12s) |
| 3 | cards | What's the limit for contactless payments on my new ca… | ❌ Weak/wrong (5s) | ⚠️ Partial (9s) |
| 4 | cards | Can I link my card to Apple Pay and also to Google Pay… | ✅ Honest (declined) (4s) | ❌ Hallucinated (answered anyway) (14s) |
| 5 | fundstransfer | What's the difference between a wire transfer and an i… | ✅ Honest (declined) (4s) | ❌ Hallucinated (answered anyway) (18s) |
| 6 | fundstransfer | Hey, i tried to send $500 to mom but it says error, pl… | ✅ Honest (declined) (5s) | ✅ Honest (declined) (17s) |
| 7 | insurance | Hey, i cant see my insurance doc in the app, wher is i… | ✅ Honest (declined) (4s) | ✅ Honest (declined) (13s) |
| 8 | insurance | Hey, i need 2nd insurace for my bike, can u help? | ❌ Weak/wrong (4s) | ⚠️ Over-cautious (declined, but a real answer existed) (11s) |
| 9 | investments | I want to change the beneficiary on my investment-link… | ⚠️ Over-cautious (declined, but a real answer existed) (5s) | ⚠️ Partial (20s) |
| 10 | investments | I want to transfer $5,000 from my checking to my broke… | ✅ Honest (declined) (5s) | ❌ Hallucinated (answered anyway) (15s) |
| 11 | loans | How does my credit card reward points affect my loan i… | ✅ Honest (declined) (4s) | ❌ Hallucinated (answered anyway) (17s) |
| 12 | loans | What happens if I miss a loan payment due to a bank ho… | ✅ Honest (declined) (4s) | ❌ Hallucinated (answered anyway) (22s) |
| 13 | security | Can I enable two-factor authentication for my savings… | ⚠️ Over-cautious (declined, but a real answer existed) (4s) | ✅ Grounded (23s) |
| 14 | security | I moved to a new address and updated it online, but I… | ✅ Honest (declined) (4s) | ✅ Honest (declined) (13s) |

*("Grounded"/"Partial"/"Weak" come from a crude content-word-overlap score against the real FAQ answer — a rough proxy, not a correctness judgement. Read the full answers below for the real picture on any row that looks surprising.)*

## Full answers

### 1. [accounts] I need to add a joint user to my savings account, what's required?

**Real FAQ answer (reference):** You can, as long as the first account holder is a senior citizen.

**Agent — ⚠️ Partial (33% grounded, 7.9s):** Adding a joint user to your Savings account is straightforward. The person you’re adding will need to provide a valid photo ID (such as a passport, driver’s licence or Aadhaar) and proof of address (utility bill, bank statement, etc.). Once you have those documents, you can submit the joint‑applicant form either at a branch or through the online account‑opening flow, and the bank will link the new holder to your Savings account. If you need any help with the exact paperwork or where to upload it, just let me know—I’m happy to guide you through the next steps!

**Baseline — ⚠️ Partial (33% grounded, 18.2s):** Sure, I can walk you through the typical steps and documents you’ll need to add a joint user (co‑owner) to your savings account. The exact requirements can vary slightly depending on the branch and the specific type of savings account you hold, but in most cases you’ll need the following:

| Item | Why it’s needed | Typical requirements |
|------|----------------|----------------------|
| **Valid government‑issued photo ID** for **both** account holders | To verify each person’s identity | Driver’s licence, state ID, passport, or military ID (must be current and not expired) |
| **Proof of address** for the new joint holder | To confirm residency for AML/KYC regulations | Recent utility bill, bank statement, lease agreement, or mortgage statement (showing name and address, dated within the last 90 days) |
| **Social Security Number (or Tax Identification Number)** for the new joint holder | Required for tax reporting and internal record‑keeping | Usually entered on the application form; you won’t need to bring the card, just the number |
| **Signature card or signature specimen** for the new joint holder | The bank needs a verified signature for future transactions | The new joint holder signs a card or a section of the joint‑account application form |
| **Completed Joint‑Account Application** (or “Add Joint Owner” form) | Formal request to add the co‑owner to the existing account | Both parties typically sign; the existing account holder may need to provide a brief statement authorising the addition |
| **Existing account information** (account number, name on the account) | To correctly link the new owner to the right account | Usually just the account number; you’ll have it on your checkbook, online banking, or a recent statement |
| **Consent/Authorization from the current account holder** | The bank must confirm that you want to add a joint owner | A signed statement on the application form is usually sufficient |
| **Possible additional documentation** (if required) | Certain situations (e.g., minor joint owners, non‑U.S. residents) have extra rules | Birth certificate for a minor, foreign passport + visa/green‑card, etc. |

### Typical Process

1. **Gather the documents** listed above for both yourself (the primary holder) and the person you want to add.
2. **Visit a branch** (or, if your bank offers it, use a secure online “Add Joint Owner” portal). Most banks require an in‑person visit for a joint‑account addition because signatures must be witnessed.
3. **Fill out the joint‑account application** (or “Add Joint Owner” form). Both parties will need to provide personal details, IDs, and signatures.
4. **Submit the IDs and proof‑of‑address**. A bank representative will make copies and keep the originals for verification.
5. **Review account terms** together. Adding a joint owner usually gives that person the same rights as you—full access to deposits, withdrawals, and the ability to close the account. Make sure you both understand the responsibilities.
6. **Pay any applicable fees** (some savings accounts have a small “joint‑owner addition” fee, typically $10–$25, though many accounts waive it for existing customers).
7. **Receive confirmation**. Once the paperwork is processed (often the same day, but sometimes 1–2 business days), you’ll get a new account statement or an updated online view showing both names.

### Things to Keep in Mind

- **Both parties get equal rights.** The new joint holder can deposit, withdraw, and even close the account without further consent. If that’s not what you want, consider a “restricted joint” or “authorized user” arrangement (some banks offer limited‑access options).
- **Credit checks are uncommon** for simply adding a joint owner to a savings account, but some banks may run a soft check for verification purposes.
- **Tax reporting.** Interest earned on the account will be reported to the IRS under both owners’ Social Security Numbers. You’ll each receive a copy of the 1099‑INT at year‑end.
- **If the joint holder is a minor**, the account will typically be a “custodial” or “UTMA/UGMA” account, which has special rules about withdrawals and transfers.
- **Existing account restrictions.** A few high‑yield or promotional savings accounts may not allow joint ownership. If you’re on a product that has that limitation, the representative will let you know and may suggest switching to a regular savings product.

### Quick Checklist

- [ ] Valid photo ID for both parties  
- [ ] Proof of address for the new joint holder  
- [ ] Social Security Number (or TIN) for the new joint holder  
- [ ] Completed joint‑account addition form (both signatures)  
- [ ] Any extra docs (minor’s birth certificate, foreign ID, etc.)  
- [ ] Ready to cover a small processing fee (if applicable)

---

**Next steps:** If you’re ready, the fastest way is to call your local branch and schedule a brief appointment—this reduces wait time and ensures a staff member is ready to help you with the paperwork. If you prefer, you can also start the request online (if your bank supports it); you’ll receive a secure link to upload scans of the IDs, and a representative will contact you to finalize the signatures.

If you have any particular concerns (e.g., adding a minor, moving to a different type of savings product, or avoiding fees), just let me know and I can tailor the guidance further. Happy to help!

### 2. [accounts] Can I link my savings account to my new debit card?

**Real FAQ answer (reference):** No. You can only link the Sweep-In facility to the accounts with the same account title. For example, a Fixed Deposit held by A-B can be linked to a Savings Account held by A-B across branches.

**Agent — ⚠️ Over-cautious (declined, but a real answer existed) (12% grounded, 3.7s):** I’m sorry, but I don’t have information about linking a savings account to a debit card in my reference material. For help with that, please reach out to our customer‑support team—they’ll be able to walk you through the process.

**Baseline — ⚠️ Over-cautious (declined, but a real answer existed) (44% grounded, 11.6s):** **Answer**

Hi ! Thanks for reaching out. I’m happy to help you with linking your savings account to your new debit card.

---

### 1. What most banks do
- **Typical setup:** Debit cards are usually issued for a *checking (or current) account* because they are meant for everyday spending and bill‑pay where unlimited transactions are allowed.
- **Savings accounts:** Many banks also let you **link a debit card to a savings account**, but there are usually a few extra rules (e.g., a limit on the number of withdrawals per month, or the card may be “read‑only” for ATM cash‑only).

### 2. Does our bank allow it?
Yes – our bank lets you attach a debit card to a savings account, but:

| Feature | When linked to **checking** | When linked to **savings** |
|---------|----------------------------|-----------------------------|
| Point‑of‑sale purchases (POS) | ✅ Unlimited | ✅ Allowed, but some merchants may block “savings‑only” cards |
| ATM cash withdrawals | ✅ Unlimited | ✅ Allowed, up to **6 withdrawals per statement cycle** (federal regulation, though we’ve waived it for most digital‑only accounts) |
| Online bill‑pay / ACH | ✅ Unlimited | ✅ Works, but you’ll see the same limits on withdrawals |
| Overdraft protection | ✅ Available (if you opt‑in) | ❌ Not available – a savings‑linked card can’t overdraft |

If you only need the card for ATM cash and occasional online purchases, linking it to your savings account works fine.

---

### 3. How to link the card to your savings account

You have three easy ways:

| Method | Steps |
|--------|-------|
| **Mobile app** | 1. Open the app & tap **“Cards”** → **“Add/Link Card.”** <br>2. Choose **“Link to existing account.”** <br>3. Select **“Savings – [Your Account #]”.** <br>4. Confirm with your PIN or biometric. <br>5. Card will be activated for that account within a few minutes. |
| **Online banking portal** | 1. Log in at **online.bank.com**. <br>2. Go to **“Accounts & Cards” → “Debit Cards.”** <br>3. Click **“Link Card to Account.”** <br>4. Pick your savings account from the drop‑down and click **“Save.”** |
| **Phone / branch visit** | Call our 24‑hour support line (1‑800‑555‑BANK) or stop by any branch. Provide your card number and savings account number; a representative will link it for you in real time. |

> **Tip:** After linking, you’ll need to **activate the card** (if you haven’t already) by making a $0‑$5 purchase or using an ATM.

---

### 4. Things to keep in mind

1. **Withdrawal limits** – If you exceed the monthly free‑withdrawal count, a small fee may apply (usually $2‑$3 per excess transaction).  
2. **Interest impact** – Frequent withdrawals from a savings account can reduce the average daily balance, possibly lowering the interest you earn.  
3. **Security** – The same fraud‑protection features (e‑alerts, zero‑liability) apply regardless of the linked account.  
4. **Changing the link later** – You can re‑link the card to a checking account at any time via the app or by calling us.

---

### 5. Next steps for you

1. **Open the mobile app** (or log into online banking).  
2. Follow the “Link Card to Account” steps above.  
3. If you run into any error messages or prefer not to do it yourself, just give us a call at **1‑800‑555‑BANK** (option 2 for “Debit Card Assistance”), and we’ll handle it for you.

---

#### Need more help?
- **If you’d like a step‑by‑step walkthrough** over the phone, let us know and we’ll schedule a quick call.  
- **If you want a different card** (e.g., a checking‑linked debit card with overdraft protection), we can issue a new one right away at no extra charge.

Feel free to reply here or call the number above—happy to assist further!

### 3. [cards] What's the limit for contactless payments on my new card?

**Real FAQ answer (reference):** The Contactless technology works when the card is waved at a maximum range of 4 cms. Hence, even if the customer is at a small distance from the terminal, no accidental transaction can take place, Plus the cashier must first enter the amount on the PoS machine before the card is tapped/ waved and the payment is processed

**Agent — ❌ Weak/wrong (10% grounded, 4.8s):** For contactless purchases there’s no set upper limit – you can spend up to the amount you have available on the card. The only restriction is your card’s balance. (The  ₹10,000  limit you sometimes see applies to cash‑withdrawal transactions, not to point‑of‑sale or contactless payments.) If you have any other questions about your new card, just let me know!

**Baseline — ⚠️ Partial (26% grounded, 9.1s):** Hi ! The contactless‑payment limit is set by the card scheme and can vary a little depending on where you’re located, but most of our new debit and credit cards have a default contact‑less ceiling of **£45 / €50 / $50 per tap**.  

A few quick things to keep in mind:

| Region | Standard contact‑less limit* |
|--------|-----------------------------|
| United Kingdom | £45 per transaction |
| Euro‑area | €50 per transaction |
| United States & Canada | $50 per transaction |
| Australia & New Zealand | AU$100 per transaction |

\*If you exceed the limit, the terminal will automatically ask you to insert the card and enter your PIN, after which the contact‑less feature is re‑enabled.

**You can raise the limit** (or remove it completely) by:

1. **Performing a chip‑&‑PIN transaction** for a purchase that’s higher than the current limit. The system records that you’ve verified your PIN, and the limit is usually increased to the card‑specific maximum (often up to £100/€100/$100).  
2. **Changing the setting in the mobile banking app** (if you have a “Security & Limits” section). Some cards let you choose a higher contact‑less ceiling up to the maximum allowed by the card scheme.  
3. **Visiting a branch or calling us** – we can adjust the limit for you after confirming your identity.

If you’re not sure which exact limit applies to your specific card, the fastest way to check is:

1. Open the **Bank App** → *Cards* → select the card → *Contact‑less limit*.  
2. Or look at the **paper/card‑holder agreement** that came with your card – the limit is listed in the “Contact‑less payments” section.

**Need a higher limit right away?**  
Just make a chip‑and‑PIN purchase that’s above the current limit (for example, a $60 grocery run). After the transaction is approved, the contact‑less limit will be reset to the higher tier.

If you have any trouble locating the setting, or if you’d like us to manually adjust the limit for you, just let us know the last four digits of the card (you can type them here) and we’ll take care of it once we verify your identity.  

Hope that helps! Let me know if there’s anything else you’d like to know.

### 4. [cards] Can I link my card to Apple Pay and also to Google Pay simultaneously?

**Real FAQ answer (reference):** (no match found)

**Agent — ✅ Honest (declined) (0% grounded, 3.6s):** I’m sorry—I don’t have a specific answer to that in our FAQ. For the most accurate information about using your card with Apple Pay and Google Pay at the same time, please reach out to our customer‑support team. They’ll be happy to help you set it up.

**Baseline — ❌ Hallucinated (answered anyway) (0% grounded, 14.5s):** **Short answer:** Yes – in most cases you can add the same debit or credit card to both Apple Pay and Google Pay at the same time.

**What you need to know**

| Topic | Details |
|-------|----------|
| **Eligibility** | Your card must be enrolled in our “mobile‑wallet” program and be a Visa, Mastercard, Discover, or American Express (or any other network we support). If you’re not sure, you can check the “Card Details” section in online banking or give us a quick call. |
| **Multiple wallets** | Adding the card to one wallet does **not** remove it from another. You can have the card in Apple Pay, Google Pay, Samsung Pay, or any other supported digital wallet simultaneously. |
| **Device requirements** | <ul><li>iPhone 6 or newer with iOS 10+ (or an Apple Watch) for Apple Pay.</li><li>Android 5.0+ with Google Play Services Version 21.0+ for Google Pay.</li></ul>Make sure your device’s OS is up‑to‑date. |
| **Security** | Both wallets use tokenization – a unique device‑specific token replaces your actual card number, so the merchant never sees the real PAN. If a device is lost or stolen, you can remotely suspend the wallet without affecting the card itself. |
| **Fees** | There are no extra fees from the bank for adding the card to either wallet. Any merchant‑imposed surcharge would be the same as a regular contact‑less transaction. |
| **Limits & controls** | <ul><li>You can set daily/weekly spending limits for contact‑less payments in your online banking settings.</li><li>You can disable a specific wallet (e.g., Google Pay) at any time from the “Manage Cards” section.</li></ul> |
| **Potential exceptions** | A very small number of premium or corporate cards may be restricted to a single wallet for security or compliance reasons. If you receive an error while adding, let us know and we’ll verify the card’s eligibility. |

**How to add the card**

1. **Apple Pay**  
   - Open **Wallet** on your iPhone (or Settings → Wallet & Apple Pay).  
   - Tap **Add Card** → **Credit/Debit Card**.  
   - Use the camera to capture your card or enter the details manually.  
   - Follow the verification steps (usually a one‑time passcode sent via SMS or email).  
   - Once approved, the card will appear in Wallet and you can start tapping.

2. **Google Pay**  
   - Download/open the **Google Pay** app from the Play Store.  
   - Tap **Payment methods** → **Add card** → **Credit or debit card**.  
   - Scan the card or type the number, expiration, CVV.  
   - Verify via SMS/email if prompted.  
   - After approval, the card will be ready for tap‑to‑pay.

**What to do if you run into trouble**

- **Error “Card not supported”** – double‑check that the card type is listed in our mobile‑wallet FAQs, or contact us with the last four digits so we can confirm eligibility.  
- **Verification code not received** – ensure your mobile number/email is up‑to‑date in our system, and check any spam filters.  
- **Card not appearing after a successful add** – restart the device and open the wallet app again; if the problem persists, let us know.

**Need further help?**  
If you’d like us to confirm that your specific card can be added to both wallets, or if you need step‑by‑step assistance on a particular device, just reply with the last four digits of the card (or call the support line) and we’ll take care of the rest.

### 5. [fundstransfer] What's the difference between a wire transfer and an internal transfer?

**Real FAQ answer (reference):** (no match found)

**Agent — ✅ Honest (declined) (0% grounded, 4.0s):** I’m sorry—I don’t have a specific FAQ entry that explains how a wire transfer differs from an internal transfer. For the most accurate information, please reach out to our live customer‑support team. They’ll be able to walk you through the details and help you choose the right option for your needs.

**Baseline — ❌ Hallucinated (answered anyway) (0% grounded, 18.3s):** **Wire Transfer vs. Internal Transfer**

| Feature | **Wire Transfer** | **Internal Transfer** |
|---------|-------------------|------------------------|
| **What it is** | An electronic movement of funds **between two different financial institutions** (e.g., from your account at Bank A to an account at Bank B, or to a recipient’s account at another bank). | A movement of funds **between accounts you already hold at the same bank** (e.g., from your checking to your savings, or from your personal account to a joint account you also own). |
| **Typical uses** | • Paying a seller or service provider who banks elsewhere <br>• Sending money to family/friends who have accounts at another bank <br>• International payments (SWIFT) | • Re‑balancing your own accounts <br>• Paying a credit‑card bill linked to the same bank <br>• Transferring money to a linked account (e.g., from a checking to a linked investment account) |
| **Speed** | • Domestic wires: usually **same‑day** (often within a few hours, but can take until the next business day depending on cut‑off times). <br>• International wires: **1–3 business days** (often longer if intermediary banks are involved). | • Usually **instant** or within a few minutes, because the money never leaves the bank’s internal system. Some banks may batch transfers overnight, but most show up immediately in the destination account. |
| **Cost** | • Typically a **fee** (≈ $20‑$35 for outgoing domestic wires; $30‑$50+ for international wires). <br>• Receiving banks may also charge a small fee. | • **Free** in most cases, especially when moving money between your own accounts. Some banks charge a fee for certain external‑account transfers, but internal ones are normally free. |
| **Information required** | • Recipient’s full name, address, and bank details (routing/ABA number for U.S., SWIFT/BIC for international). <br>• Recipient account number. <br>• For international wires, sometimes the purpose of payment and the recipient’s bank’s IBAN. | • Only the **account number** (or a nickname) of the destination account you already hold at the same bank. No routing or external bank details are needed. |
| **Security & verification** | • More layers of verification (e.g., additional authentication, sometimes a “wire‑only” password). <br>• Once sent, it’s hard to reverse. | • Handled inside the bank’s secure environment; you can usually cancel or edit a transfer before it’s processed (often within a few minutes). |
| **Limits** | • May have daily or per‑transaction limits set by the bank, especially for large corporate wires. <br>• International wires can be subject to additional compliance checks. | • Usually limited only by the balance in the source account, but some banks impose a modest daily cap on free internal transfers for security reasons. |
| **Regulatory compliance** | • Subject to anti‑money‑laundering (AML) checks, especially for cross‑border transfers. <br>• Often requires you to confirm the purpose of the payment. | • Still subject to AML monitoring, but because the funds stay within the same institution, the process is simpler and faster. |

### Quick Take‑aways
- **Use a wire transfer** when you need to send money **outside of our bank** (to another bank or to an overseas account). It’s fast, but it usually costs a fee and requires more detailed recipient information.
- **Use an internal transfer** when you’re moving money **between your own accounts at our bank**. It’s essentially instantaneous, free, and needs only the destination account number.

### Need Help Setting Up Either Transfer?
- **Wire Transfer:** Let us know the destination bank details (routing/SWIFT, account number, recipient name) and whether it’s domestic or international. We’ll confirm the applicable fees and cut‑off times.
- **Internal Transfer:** Just tell us which of your accounts you’d like to move funds from and to (e.g., “move $500 from my checking to my savings”). If you prefer to set up a recurring internal transfer, we can arrange that as well.

Feel free to reply with the type of transfer you’d like to make, and I’ll walk you through the exact steps or schedule it for you.

### 6. [fundstransfer] Hey, i tried to send $500 to mom but it says error, plz help

**Real FAQ answer (reference):** (no match found)

**Agent — ✅ Honest (declined) (0% grounded, 4.5s):** I’m sorry you’re seeing an error when trying to send money to your mom. The FAQ doesn’t cover this specific situation, so the quickest way to resolve it is to reach out to our Customer Support team. They can look at the details of your transfer and help get it sorted out right away. If you need the contact number or instructions on how to connect through the app, just let me know!

**Baseline — ✅ Honest (declined) (0% grounded, 16.7s):** Hello! I’m sorry you’re running into an error when trying to send $500 to your mom. Let’s see if we can get this sorted out quickly.

### Common reasons a transfer might fail
| Reason | What to check |
|--------|----------------|
| **Insufficient funds** | Make sure your account balance covers the $500 + any applicable fees. |
| **Transfer limits** | Some accounts have daily or per‑transaction limits (e.g., $1,000 daily for standard users). |
| **Recipient details** | Verify the account number, routing number, or email/phone (if using person‑to‑person) is entered correctly. |
| **Security/verification** | A recent security flag (e.g., unusual location, device) can block the transaction until you confirm it. |
| **Technical glitch** | Occasionally a temporary service issue can cause an error. Refresh the app or try again after a few minutes. |
| **Bank‑to‑bank (ACH) vs. internal transfer** | ACH transfers can be delayed or rejected if the receiving bank rejects the details. Internal “Bank‑to‑Bank” transfers between two accounts at our bank are usually instant. |

### Quick troubleshooting steps
1. **Check your balance** – Ensure you have at least $500 + any fee.
2. **Confirm the amount and recipient** – Double‑check the account number/routing or the contact you selected for the transfer.
3. **Review any error code/message** – If the app shows a code (e.g., “ERR‑01”, “Insufficient funds”), note it— it helps us pinpoint the issue.
4. **Try again** – Sometimes re‑entering the details or restarting the app resolves a transient error.
5. **Look for alerts** – In the app’s “Messages” or “Security” section, see if we asked you to verify the transfer.

### If it still won’t go through
Please reply with any of the following (you can share as much as you’re comfortable with; we’ll only use it to help you resolve the issue):

- The **exact error message** or error code you’re seeing.
- The **type of transfer** you’re attempting (e.g., “Send Money to a contact”, “External ACH transfer”, “Wire”).
- The **date/time** you tried the transfer.
- Whether you’re using the **mobile app**, **online banking website**, or **phone banking**.
- If you have **any security alerts** in the app (e.g., “Verify transfer” prompts).

Once we have that information, we can:

- Verify if the $500 exceeds any limits on your account.
- Confirm that the recipient’s details are valid.
- Reset any security blocks that might be holding the transaction.
- If needed, open a support ticket for you and provide a direct escalation path.

### In the meantime
If you need the money to reach your mom urgently, you could:
- Use a **different payment method** (e.g., another linked debit card or a peer‑to‑peer service) as a temporary workaround.
- **Visit a branch** or call our 24/7 phone line (1‑800‑XXX‑BANK) and ask the representative to process the transfer manually.

---

**Please let me know the details above, and I’ll look into this right away!** If you prefer to speak with a live agent, just let me know and I can provide the phone number or arrange a secure chat.

### 7. [insurance] Hey, i cant see my insurance doc in the app, wher is it?

**Real FAQ answer (reference):** (no match found)

**Agent — ✅ Honest (declined) (0% grounded, 4.4s):** I’m sorry I don’t have the information you need in my FAQ database. For help locating your insurance documents in the app, please get in touch with our customer‑support team—they’ll be able to walk you through where to find them. If you need anything else, just let me know!

**Baseline — ✅ Honest (declined) (0% grounded, 12.9s):** Hey there! I’m sorry you’re having trouble locating your insurance document in the app. Let’s get you back on track.

### Where the insurance document usually lives
1. **Open the app** and tap **“My Products”** (or “Accounts & Services”) from the main menu.  
2. Look for a section titled **“Insurance”**, **“Policies”**, or **“Insurance & Protection.”**  
3. Inside that section you should see a list of any insurance policies you’ve purchased through us.  
4. Tap the policy you need → **“View Document”** or **“Download PDF.”**  

If you don’t see an “Insurance” heading at all, it could be one of the following:

| Why it might be missing | What to do |
|--------------------------|------------|
| **You haven’t added an insurance product yet** | Go to **“Shop Products” → Insurance** and add the policy you need. Once the policy is active, the document will appear in the steps above. |
| **The policy is from a third‑party insurer not linked to our app** | You’ll need to log in to that insurer’s own app/website to view the document, or you can request us to link it (provide the policy number and insurer name). |
| **App needs an update** | Check the Play Store / App Store for the latest version, install it, then repeat the steps. |
| **Cache or login glitch** | Log out of the app, close it completely, reopen, and log back in. This often forces a refresh of the product list. |

### Quick troubleshooting checklist
1. **Update the app** – make sure you’re running the most recent version.  
2. **Refresh the screen** – pull down on the “My Products” page to force a sync.  
3. **Clear cache (Android)** – Settings → Apps → Your Bank App → Storage → Clear Cache. (iOS doesn’t have a manual cache clear; just reinstall if needed.)  
4. **Re‑login** – sometimes a fresh login pulls in the latest policy data.  

### Still can’t find it?
If after trying the above you still don’t see the document, please let me know:

- Your **full name** (as it appears on the account)  
- The **type of insurance** (e.g., life, travel, home, auto)  
- The **policy number** (if you have it handy)  

You can send that information securely via the in‑app chat or give us a call at the number on the back of your debit/credit card. We’ll pull up your policy and either push the document to the app for you or email it directly.

Let me know how it goes, and I’ll be happy to help further!

### 8. [insurance] Hey, i need 2nd insurace for my bike, can u help?

**Real FAQ answer (reference):** Call our toll-free helpline 1800-2-700-700 and weâ€™ll advise you how to proceed. You may have to pay a small fee for a duplicate policy.

**Agent — ❌ Weak/wrong (6% grounded, 3.6s):** Absolutely, you can add a second insurance policy for your bike. It’s allowed as long as the underwriting process approves the additional coverage. If you’d like to move forward, I can help start the application or answer any other questions you have.

**Baseline — ⚠️ Over-cautious (declined, but a real answer existed) (38% grounded, 11.2s):** Hi there! I’d be happy to help you explore a second bike insurance policy.

**Here’s how we can get started:**

1. **Check your current coverage**  
   - If you already have a policy with us (or another insurer), let us know the basic details (e.g., insurer name, coverage type). This helps us avoid duplicate coverage and find the best complementary plan.

2. **Gather a few details about your bike**  
   - **Make & model**  
   - **Year of manufacture**  
   - **Engine capacity (cc)**  
   - **Registered location (city/postcode)**  
   These details are used only to generate an accurate quote.

3. **Choose the coverage you need**  
   - **Liability only** – protects third parties if you’re at fault.  
   - **Comprehensive** – covers theft, fire, accidental damage, and third‑party liability.  
   - **Add‑ons** – roadside assistance, personal accident, accessories coverage, etc.

4. **Get a quick, free quote**  
   You can obtain an instant quote in three ways:  
   - **Online**: Log into your banking app, go to *Products → Insurance → Bike Insurance* and follow the “Get a Quote” flow.  
   - **Phone**: Call our dedicated insurance line at **1‑800‑555‑BANK** (Mon‑Fri 9 am‑6 pm). Have the bike details handy and a representative will walk you through the options.  
   - **Chat**: If you’re using the web‑chat widget on our website, just type “Bike insurance quote” and a specialist will take over.

5. **Complete the application**  
   Once you’ve chosen a plan, you’ll need to confirm a few things for regulatory purposes:  
   - Your **full name** and **date of birth** (to verify identity).  
   - Your **bank account number** (if you’d like premiums deducted automatically).  
   - A **copy of the bike’s registration (RC) certificate** (you can upload a photo in the app).  

   *We never ask for passwords, PINs, or full credit‑card numbers in a chat.*

6. **Policy issuance**  
   After the brief underwriting review (usually within minutes), you’ll receive an electronic policy document via email and in the “Insurance” section of your banking app. You can print it, share it, or keep it digitally.

---

### Quick next step
If you’d like me to start a quote right now, just let me know the bike details listed in step 2 (make, model, year, engine size, and where it’s registered). I’ll generate a preliminary estimate and then guide you through the rest of the process.

If you prefer to speak with a human agent, just say “talk to an agent” and I’ll connect you.

Looking forward to helping you get the coverage you need! 🚲✨

### 9. [investments] I want to change the beneficiary on my investment-linked life insurance policy, how?

**Real FAQ answer (reference):** No. You choose your maturity benefit option and death benefit option at policy inception and they cannot be changed during the policy term.

**Agent — ⚠️ Over-cautious (declined, but a real answer existed) (8% grounded, 5.0s):** I’m sorry—I don’t have the specific details on how to change the beneficiary for an investment‑linked life insurance policy. For the most accurate and secure assistance, please contact our dedicated insurance support team or visit a branch where a representative can guide you through the process. If you need anything else, just let me know!

**Baseline — ⚠️ Partial (25% grounded, 20.0s):** **Changing the beneficiary on your investment‑linked life insurance policy**

Below is the usual process we follow for all of our investment‑linked life insurance products. The exact steps may vary slightly depending on the specific policy you have, but these are the core actions you’ll need to take:

---

### 1. Verify Your Identity
For any change to a life‑insurance contract we must first confirm that you are the policyholder (or an authorised representative). Have one of the following ready:

| What you’ll need | Why it’s required |
|------------------|-------------------|
| **Valid photo ID** (e.g., passport, driver’s licence, or national ID card) | To match the name on the policy |
| **Policy number** (you’ll find it on your policy document, annual statement or the online portal) | To locate the correct contract |
| **Recent proof of address** (utility bill, bank statement, etc.) – if you haven’t updated your address with us in the last 12 months | To satisfy regulatory “Know‑Your‑Customer” checks |
| **A signed beneficiary‑change form** (if you’re doing it on paper) | Legal authorisation of the change |

You do **not** need to send copies of these documents in the chat. When you contact us through a secure channel (phone, secure message in the banking app, or in‑branch), we’ll ask you to upload or present them.

---

### 2. Choose Your Preferred Channel

| Channel | How to start | Typical turnaround |
|--------|--------------|--------------------|
| **Online banking / Mobile app** | Log in → “Insurance & Investments” → select your policy → “Manage Beneficiary” | 1–3 business days (after document upload) |
| **Secure e‑mail / In‑app message** | Use the “Secure Message” feature in the app or our online banking portal | 1–2 business days |
| **Phone (call centre)** | Dial the dedicated insurance line (usually 1800 XXXX or the number shown on your policy document) | Immediate guidance; the form can be faxed or emailed |
| **Branch visit** | Walk into any branch with your ID and policy documents | Same‑day processing if the form is completed on the spot |

> **Tip:** Using the mobile app or online portal is the fastest way because the system can auto‑populate your existing details and the uploaded documents are processed automatically.

---

### 3. Fill Out the Beneficiary‑Change Form

- **New Beneficiary Details** – full name, relationship to you, date of birth, and contact address.
- **Percentage Allocation** – if you are naming more than one person, state the exact share each will receive (e.g., 60 % to Jane Doe, 40 % to John Smith). The total must equal 100 %.
- **Signature** – your handwritten signature (if paper) or electronic signature (if online). Some jurisdictions require a second signature from a witness; the online form will prompt you if that’s needed.
- **Declaration** – a short statement confirming you are making the change voluntarily and that the information is correct.

If you are changing a **contingent (secondary) beneficiary**, be sure to tick the appropriate box; the system will treat it separately from the primary beneficiary.

---

### 4. Submit & Confirm

1. **Submit** the completed form (online upload, fax, email attachment, or hand‑in at the branch).  
2. **Receive a Confirmation** – you’ll get a reference number via SMS/e‑mail and a PDF of the updated policy schedule within 1–3 business days.  
3. **Review** the confirmation to ensure the names, percentages, and spelling are correct. If anything looks off, contact us immediately (refer to the reference number).

---

### 5. What to Expect After the Change

| Item | Details |
|------|---------|
| **Policy coverage** | Remains unchanged; only the payout direction is updated. |
| **Tax implications** | In most jurisdictions the beneficiary designation itself does not trigger tax, but it can affect estate‑tax planning. If you’re unsure, consult a tax adviser. |
| **Future changes** | You can modify the beneficiary again later using the same process. Some policies allow *online* changes only once per calendar year; check the policy wording if you anticipate frequent updates. |
| **Notification to the insurer** | The insurer will send a formal “Beneficiary Update Letter” to the new beneficiary (if you opt‑in). If you prefer privacy, you can request that they don’t send any notice. |

---

## Quick Checklist Before You Contact Us

- [ ] Policy number at hand  
- [ ] Valid photo ID (and proof of address if needed)  
- [ ] Full details of the new beneficiary(ies) – name, DOB, relationship, address, % share  
- [ ] Completed beneficiary‑change form (paper or ready to fill online)  

---

### Need a Direct Link?

If you’re ready to start online, click the **“Change Beneficiary”** button in the insurance section of our banking app or log in to our web portal and navigate to:

```
[My Accounts] → [Insurance & Investments] → [Your Policy] → [Manage Beneficiary]
```

The system will guide you through each field and let you upload the necessary documents in a secure, encrypted session.

---

## Still Have Questions?

- **Phone support:** Call **1800 XXXX** (available 8 am – 8 pm, Mon‑Fri) and ask for “Beneficiary change – investment‑linked life insurance”.
- **Secure chat:** Use the in‑app chat and select “Insurance – Policy Changes”.
- **Branch assistance:** Any branch representative can pull up your policy and give you a paper form on the spot.

We’re here to make the process smooth and secure. Let us know which channel you’d prefer, and we’ll walk you through the next steps!

### 10. [investments] I want to transfer $5,000 from my checking to my brokerage, what's the fastest way?

**Real FAQ answer (reference):** (no match found)

**Agent — ✅ Honest (declined) (0% grounded, 4.7s):** I’m sorry—I don’t have a specific FAQ entry that covers the fastest way to move $5,000 from your checking account to a brokerage account. For detailed guidance on the quickest transfer method, please reach out to our human customer‑support team. They’ll be able to walk you through the options and any applicable limits or processing times.

**Baseline — ❌ Hallucinated (answered anyway) (0% grounded, 15.1s):** **Fastest way to move $5,000 from your checking account to a brokerage**

| Method | Typical speed | Typical cost | When it’s the best choice |
|--------|---------------|--------------|--------------------------|
| **Internal (same‑bank) ACH transfer** | Usually **same‑day** (often within a few minutes if both accounts are with us) | Free | Your brokerage is also a customer of our bank or you’ve added it as an “internal” account in Online Banking. |
| **External ACH transfer** | 1‑2 business days (same‑day ACH is possible if you request it) | Free – may have a small fee for same‑day ACH ($0‑$5) | Brokerage is at a different institution but supports ACH deposits. |
| **Wire transfer** | **Same‑day** (usually by 4 PM ET) | $25‑$30 outbound wire fee | You need the money in the brokerage **today** and the brokerage accepts wires. |
| **Instant‑payment services (e.g., Zelle, PayPal)** | Minutes | Depends on the service (usually free for bank‑to‑bank) | Brokerage allows deposits via those services (less common). |

### Recommended steps (Internal ACH – fastest & free)

1. **Log in** to our Mobile Banking app or Online Banking portal.  
2. Go to **“Transfers & Payments”** → **“Transfer Between My Accounts.”**  
3. **Select your checking account** as the *From* account.  
4. In the *To* dropdown, choose **“Add a new external account.”**  
   - Enter the brokerage’s routing number and your brokerage account number (you can find these on the brokerage’s deposit page).  
   - Check the box for **“Same‑day ACH”** if you need the money today.  
5. **Enter $5,000** as the amount and give the transfer a memorable description (e.g., “Brokerage deposit”).  
6. Review the details, then **confirm** the transfer.  
7. You’ll receive an on‑screen confirmation and a push‑notification/email receipt.

*If the brokerage is already set up as an internal account (i.e., it’s a subsidiary of our bank), the transfer will post instantly—often within a few minutes.*  

### If you need the money **today** and the brokerage only accepts wires

1. Call the **Customer Service line** (1‑800‑XXX‑XXXX) or use the secure chat to request an **outbound wire**.  
2. Provide:  
   - Brokerage name & address  
   - Routing (ABA) number  
   - Your brokerage account number  
   - Amount ($5,000)  
3. Verify the wire fee (currently $25) and confirm the transaction.  
4. The wire will be sent that same business day (as long as the request is placed before the cutoff – typically 3:30 PM ET).  

### Quick checklist before you start

- **Confirm the brokerage’s deposit method** (ACH, wire, or both).  
- **Check your daily transfer limit** – most checking accounts allow at least $10,000 per day, but if you have a lower limit you may need to request a temporary raise.  
- **Make sure the routing and account numbers are correct**; an incorrect entry can cause a delay or a return.  
- **Verify any fees** (wire fees) and that the brokerage won’t charge its own inbound‑deposit fee.  

### Need help setting up the brokerage as a payee?

- In the app, tap **“Add New Account”** and follow the on‑screen prompts.  
- You can also schedule a quick **virtual appointment** with a Banking Associate—just let us know a convenient time and we’ll send a meeting link.  

### TL;DR

- **Fastest & free:** Internal same‑day ACH (usually minutes).  
- **If same‑day is required and ACH isn’t enough:** Outbound wire (same‑day, $25 fee).  

Let us know if you’d like us to:

- Walk you through the setup step‑by‑step in the app, **or**  
- Initiate a wire on your behalf, **or**  
- Check your daily transfer limit.

We’re here to make the transfer painless—just reply with whichever option you’d like to pursue!

### 11. [loans] How does my credit card reward points affect my loan interest calculation?

**Real FAQ answer (reference):** (no match found)

**Agent — ✅ Honest (declined) (0% grounded, 3.9s):** I’m sorry, but our FAQ doesn’t cover how credit‑card reward points might impact the interest rate on a loan. For a detailed answer, please reach out to one of our human customer‑service representatives—they’ll be able to look into your specific situation.

**Baseline — ❌ Hallucinated (answered anyway) (0% grounded, 16.6s):** **Hello! I’m happy to help clear this up.**  

### Short answer
Your credit‑card reward points do **not** change the interest rate that is applied to a loan (personal loan, auto loan, mortgage, etc.). The loan’s interest is calculated based only on the loan’s agreed‑upon rate, the outstanding balance, and the repayment schedule.  

### How points can still help you lower the cost of a loan
While points don’t affect the *rate* itself, you can use them in ways that reduce the amount of interest you actually pay:

| What you can do with points | How it impacts your loan |
|------------------------------|--------------------------|
| **Redeem for cash** (e.g., a statement credit, direct deposit, or a check) | You can apply that cash toward the loan principal. A lower principal means less interest accrues from that point forward. |
| **Redeem for a statement credit** on your credit‑card bill | Paying down the credit‑card balance faster can free up cash that you can then use to make extra payments on the loan, again reducing the outstanding balance. |
| **Convert points to travel, gift cards, merchandise, etc.** | This doesn’t affect the loan directly, but if you would have spent cash on those items, you can keep that cash available to make additional loan payments. |
| **Special “points‑toward‑loan” promotions** (rare) | Occasionally a bank may run a limited‑time offer that lets you apply points as a direct credit toward a loan balance. In that case the points act like a one‑time payment, not a change to the interest rate. |

### What *does* determine your loan interest
1. **Nominal interest rate** (fixed or variable) that was set when you opened the loan.  
2. **Outstanding loan balance** – interest is usually calculated daily on the current balance.  
3. **Repayment schedule** – how often interest is posted (daily, monthly, etc.).  
4. **Any applicable fees or discounts** (e.g., a rate reduction for automatic payments).  

None of these factors use reward‑point balances as an input.

### Practical steps if you want to use points to save on a loan
1. **Check your reward‑point redemption options** in your online banking or the credit‑card app. Look for “cash,” “statement credit,” or “direct deposit” choices.  
2. **Redeem the points** for the cash/credit you need.  
3. **Apply the cash/credit** to your loan account: you can usually do this online by selecting “Make a payment” and choosing the loan as the destination, or you can call the loan service center and ask them to apply the amount to the principal.  
4. **Verify the payment** appears as a principal reduction on your next loan statement. This will instantly lower the interest that will accrue after that date.  

### A couple of things to keep in mind
- **Redemption value:** Most banks value points at a fixed cash‑equivalent rate (e.g., 1 point = $0.01). Make sure you know that rate before you redeem, so you can calculate how much cash you’ll actually get.  
- **Expiration:** If you have points that are about to expire, using them for a cash credit now may be more valuable than letting them lapse.  
- **Promotions & Fees:** Some redemption methods carry fees (e.g., converting points to gift cards). Choose the option that gives you the greatest cash value if your goal is to reduce loan interest.  

### Need more specific help?
If you let me know:

* the type of loan you have (personal, auto, mortgage, etc.), and  
* the name of the credit‑card rewards program (e.g., “BankX Rewards,” “Premier Points,” etc.),  

I can walk you through the exact steps to redeem your points and apply them to your loan balance.

Feel free to ask any follow‑up questions—whether it’s about how to redeem points, making extra loan payments, or anything else you’re curious about!

### 12. [loans] What happens if I miss a loan payment due to a bank holiday?

**Real FAQ answer (reference):** (no match found)

**Agent — ✅ Honest (declined) (0% grounded, 4.2s):** I’m sorry—I don’t have any information on that specific situation in our FAQ. Please reach out to our customer‑support team directly; they’ll be able to tell you exactly how a bank holiday might affect a loan payment and what steps to take.

**Baseline — ❌ Hallucinated (answered anyway) (0% grounded, 22.3s):** **Answer**

If a loan payment’s due‑date falls on a bank holiday, the payment will generally be processed on the next business day. In most cases the loan servicer treats the payment as “on time” as long as it is received (or scheduled to be received) by the end of the holiday‑affected banking day. Here’s what typically happens and what you can do to be sure you stay on track:

---

### 1. How the holiday affects the payment
| Situation | What the bank does | What it means for you |
|-----------|-------------------|----------------------|
| **Due date is a bank holiday** | The banking systems that move money are closed. Your payment will be posted on the next **business day** (the first day the banks are open). | The payment is considered timely, provided it is received on that next business day. |
| **You have an automatic (ACH) debit set up** | The ACH network also pauses on holidays, so the debit will automatically run on the next business day. | No action required; the transaction will post a day later. |
| **You make a manual online or phone payment on the holiday** | The bank may allow you to submit the request, but it won’t be processed until the next business day. | The system usually shows a “scheduled for next business day” notice—again, no late‑fee risk. |
| **You miss the next business day (e.g., you forget or can’t pay)** | The payment will be recorded as late, and the usual late‑payment rules and fees apply. | Contact us right away to discuss a grace‑period request or payment extension. |

---

### 2. Why you usually won’t be charged a late fee
Most loan agreements (mortgages, personal loans, auto loans, etc.) include a **grace‑period clause** that says a payment is not considered late if it is received on the first business day after a holiday. The key points are:

- **Payment must be credited on the next business day** (or scheduled to be posted then).  
- **You must not have missed any previous due dates** (the holiday exception only applies to the specific due date that falls on the holiday).  
- **The loan agreement or the bank’s terms and conditions** may spell out any exceptions, so it’s a good idea to double‑check your contract.

If you ever receive a late‑fee notice after a holiday, please let us know right away—we’ll verify the dates and, if appropriate, reverse the fee.

---

### 3. What you can do to avoid any confusion

| Action | How to set it up |
|--------|-----------------|
| **Schedule automatic payments** (ACH or bill‑pay) | Log in to your online banking portal → “Payments & Transfers” → “Set up recurring payment” → Choose your loan account, amount, and due‑date. The system automatically handles holidays. |
| **Set a reminder a few days before the due date** | Use the bank’s mobile app → “Alerts & Notifications” → Turn on a “Payment due” reminder 3–5 days before the due date. |
| **Make a manual payment early** | If you prefer paying yourself, submit the payment at least **one business day before** a known holiday. |
| **Check the holiday calendar** | The bank’s website publishes a list of upcoming Federal holidays and any additional “bank‑closed” dates. |
| **Contact us proactively** | If you know you’ll be unable to pay on the next business day (e.g., you’re traveling), call the loan servicing team at **1‑800‑555‑LOAN** at least 24 hours before the holiday‑adjusted due date. We can often grant a short extension or note the situation on your account. |

---

### 4. Quick checklist for the next holiday

1. **Look up the holiday date** in the bank’s calendar.  
2. **Verify your loan’s due date** (you can find it on your most recent statement or in the online portal).  
3. **If the due date = holiday**, make sure you have either:  
   - An automatic payment already in place, **or**  
   - Manually submitted the payment **before** the holiday (or scheduled it for the next business day).  
4. **Confirm the payment status** after the first business day following the holiday (you’ll see a “posted” or “processed” entry).  
5. **If anything looks off**, call or chat with us within 48 hours so we can investigate.

---

### 5. Need help right now?

- **Phone:** 1‑800‑555‑LOAN (available 24/7)  
- **Secure chat:** Log in to your online banking and click the “Chat with us” button.  
- **Email:** support@yourbank.com (include your loan number in the subject line).  

We’re happy to look at your specific loan agreement, confirm the holiday schedule, and make sure no unnecessary fees are applied.

---

**Bottom line:** A bank holiday does not automatically make a payment “late.” As long as the payment is posted on the next business day (or you’ve arranged for it to be posted then), you should be fine. If you have any doubts or need to adjust your payment method, just give us a quick call or send a message—we’ll take care of it for you.

### 13. [security] Can I enable two-factor authentication for my savings account?

**Real FAQ answer (reference):** You can have both these facilities on the same Savings Account.

**Agent — ⚠️ Over-cautious (declined, but a real answer existed) (40% grounded, 3.7s):** I’m sorry, but I don’t have information on enabling two‑factor authentication for a savings account in our FAQ. Please reach out to our customer‑support team—they’ll be able to guide you through the security options available for your account.

**Baseline — ✅ Grounded (80% grounded, 23.5s):** **Yes— you can add two‑factor authentication (2FA) to protect access to your savings‑account information and any online transactions you make with it.**  

Below is a quick overview of how it works and the steps you’ll need to follow to enable it.

---

## 1. What 2FA protects

| Action | How 2FA helps |
|--------|---------------|
| **Logging into online banking** (web or mobile) | After you enter your user name and password, you’ll be asked for a second verification code before you can get in. |
| **Initiating a transfer or payment from your savings account** | A one‑time code (or push‑approval) is required before the transaction can be completed. |
| **Changing security settings or adding new devices** | The same extra step is required, preventing unauthorized changes. |

In short, 2FA secures both **access** and **transactions** linked to your savings account.

---

## 2. Which 2FA methods do we offer?

| Method | How you receive the code | Typical use case |
|--------|--------------------------|-----------------|
| **SMS/Text Message** | A 6‑digit code sent to your registered mobile number. | Good if you prefer not to install extra apps. |
| **Authenticator App** (Google Authenticator, Authy, Microsoft Authenticator, etc.) | A time‑based code that refreshes every 30 seconds. | Most secure; works even without cell service. |
| **Push Notification** (via our mobile banking app) | Tap “Approve” or “Deny” on a notification sent to your phone. | Fast and user‑friendly. |
| **Hardware Token** (optional for corporate or high‑value accounts) | A tiny device that generates a code. | Best for users who want a completely offline method. |

You can enable **one** method or **multiple** (e.g., SMS + Authenticator) and choose which one is used for each type of activity.

---

## 3. How to enable 2FA

### If you’re already logged in (web or mobile)

1. **Go to Settings → Security**  
   – In the web portal: click the gear icon → *Security & Login*.  
   – In the mobile app: tap *Menu* → *Settings* → *Security*.

2. **Select “Two‑Factor Authentication”**  
   You’ll see the list of available methods.

3. **Choose your preferred method**  
   - **SMS:** Enter the mobile number you want to use and click *Send verification code*.  
   - **Authenticator App:** Scan the QR code shown with your app, then enter the 6‑digit code generated by the app.  
   - **Push:** Ensure the banking app is installed and notifications are enabled; toggle the “Push approval” switch.

4. **Confirm and save**  
   You’ll be asked to enter a final verification code (sent by the method you just set up) to confirm that everything works.

5. **(Optional) Add a backup method**  
   Adding a second method (e.g., SMS as backup for the authenticator app) prevents lock‑out if you lose access to the primary one.

### If you’re not yet logged in

1. **Log in with your username/password as usual.**  
2. You’ll be prompted immediately to set up 2FA if you haven’t done so; just follow the on‑screen steps.  
3. If you encounter any error messages, make sure your contact details (phone number, email) are up to date in *Profile → Personal Information*.

---

## 4. What to do if you run into trouble

| Issue | Quick fix |
|-------|-----------|
| **Didn’t receive the SMS code** | Verify the phone number in *Profile → Contact Info*; make sure you have service and that your carrier isn’t blocking short‑code messages. |
| **Authenticator app shows “Invalid code”** | Check that your device’s time is set to *automatic* (network time). If you switched phones, you’ll need to re‑scan the QR code. |
| **Lost access to my phone** | Use a backup 2FA method (SMS or backup codes). If you have none, call our 24‑hour “Security Support” line at **1‑800‑SEC‑SAFE (1‑800‑732‑7233)** – we’ll verify your identity and help you regain access. |
| **Hardware token not working** | Ensure the token’s battery is still good (most tokens last ~5 years). If it’s dead, request a replacement through *Secure Messages* or the phone line above. |

---

## 5. A few best‑practice tips

1. **Keep your phone number current** – 2FA codes are only useful if they can reach you.  
2. **Store backup codes** (if you enable them) in a safe place, e.g., a password manager or a printed copy kept in a secure drawer.  
3. **Avoid re‑using the same password** for other services; 2FA adds a layer, but a strong password is still essential.  
4. **Log out of the banking app** when you’re done, especially on shared or public devices.  
5. **Enable login alerts** (found under *Security → Login notifications*) so you’re emailed or texted whenever a new device accesses your account.

---

### Ready to set it up now?

If you’d like step‑by‑step guidance while you’re in the app or on the website, just let me know which device you’re using (web browser, iOS app, Android app) and I’ll walk you through each screen.

Otherwise, you can start the process yourself by following the steps above. Should anything feel unclear or you hit a snag, feel free to reply here, call our 24‑hour secure line (**1‑800‑SEC‑SAFE**), or send us a secure message through the online banking portal.

Welcome to a more secure banking experience! 🚀

### 14. [security] I moved to a new address and updated it online, but I think the system still shows my old one. Could this be a security risk?

**Real FAQ answer (reference):** (no match found)

**Agent — ✅ Honest (declined) (0% grounded, 3.8s):** I’m sorry—I don’t have specific information on that in our FAQ. If you suspect your address hasn’t been updated correctly, it’s a good idea to reach out to our customer‑support team right away so they can verify everything and make sure your account remains secure.

**Baseline — ✅ Honest (declined) (0% grounded, 12.8s):** Hi ! I’m sorry to hear the address change isn’t showing up yet. Let’s get this sorted so your account is up‑to‑date and secure.

### Why the old address might still appear
| Reason | What it means |
|--------|----------------|
| **System processing time** | Some back‑office updates can take up to 24‑48 hours to propagate to all internal screens. |
| **Cache or session data** | If you’re still logged in on a device that cached the old info, it will keep showing the previous address until you log out and back in (or clear the app’s cache). |
| **Partial update** | Occasionally only the mailing address updates while the “profile” address stays unchanged if the change wasn’t fully submitted. |

### Is this a security risk?
* **No immediate danger** if the old address is only displayed in your online view.  
* The real risk would be if someone could still have mail or account statements sent to the old address. That could happen if the change never fully processed or if the old address is still on file for **paper statements, debit cards, or credit‑card replacements**.

### Quick steps you can take right now
1. **Log out and log back in** (or clear the app/browser cache). This forces a fresh pull of your latest data.  
2. **Check your recent communications** (e‑mail, SMS, or paper mail). If you’re still receiving statements or alerts at the old address, let us know immediately.  
3. **Review the “Contact Information” page** in the app/online banking:  
   - Look for a line that says “Mailing address” vs. “Home address”. Make sure both (if applicable) show the new one.  
   - If you see a “Pending change” banner, it means the update is still processing.  

### If the old address still appears after 24 hours
1. **Secure message**: Open a secure message in your online banking portal (or via the app) and select “Profile/Address Update”. Include:
   - Your full name  
   - The new address (street, city, state, ZIP)  
   - A brief note: “Address still showing old version after update on [date]”
2. **Phone verification** (optional but fastest): Call our 24/7 Customer Care line • 1‑800‑XXX‑XXXX, choose “Account & Profile”. Have a photo ID handy; the rep will verify your identity and push the change through manually.  
3. **Ask for confirmation**: Request a confirmation email or secure message once the address is fully updated. This gives you a record that the change was completed.

### Preventing any future issues
- **Enable electronic statements** – that way you won’t rely on postal mail for account alerts.  
- **Set up alerts** (SMS or push) for any address‑related changes so you’re notified instantly.  
- **Periodically review your profile** after any major life event (move, name change, etc.) to confirm everything matches.

### Need more help?
If you’d rather have a representative look at this right now, just reply with “Speak to an agent” and I can arrange a callback, or you can call the number above. We’ll make sure your new address is properly recorded and that no sensitive information is being sent to the old one.

Let me know how you’d like to proceed!
