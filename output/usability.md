# Campus Customs — Usability Improvements

This document explains the four usability improvements added to the Campus Customs website and chatbot. For each, it describes what changed, how a shopper uses it, why it helps the shopper, and why it helps the business.

All four improvements use the same data: the existing `campus_customs.db` catalogue and inventory. Prices, sizes, colors, stock and images are always read from the database, never typed into the website or the chatbot. The website, the cart and the assistant therefore always agree with each other and with what is actually on the shelf.

---

## 1. Shopping Cart

### What changed

- **Add to Cart** buttons on every product card, on the Products page and in the chatbot, and on each product's detail page.
- **Size selection** before adding. Sold-out sizes are shown but cannot be picked. One-size products are added directly.
- **Stock limits** everywhere. A shopper can never add, or increase to, more units than are in stock. The product page shows how many are already in the cart and how many more are available.
- **A cart icon with an item count** in the navigation bar, visible on every page.
- **A cart page** (`/cart`) showing each item's image, name, size, unit price, quantity controls, line total and a remove button, plus an order total. The total updates instantly when quantities change. An empty cart shows a clear message and a "Browse Products" button.
- **Automatic corrections.** If an item sells out or its stock drops after it was added, the cart adjusts the quantity or removes the item and tells the shopper why.
- **The cart is kept** while the shopper moves around the site and when they refresh the page. This works for guests as well as logged-in customers.

### Why it helps the shopper

- **They can collect items as they browse,** instead of deciding on each product one at a time or keeping a list in their head.
- **They never pick something that can't be bought.** Sold-out sizes are visible but disabled, and quantities are capped at real stock, so there is no disappointment at checkout.
- **The running total is always visible,** which makes it easy to stay within a budget, for example a parent buying gifts for several family members.
- **They can add to the cart from wherever they are:** a product card, the product page, or a product the chatbot just recommended.

### Why it helps the business

- **The online catalogue becomes a shop.** Before, the site could show products but customers had nowhere to collect what they wanted; the cart is the first step toward online sales.
- **Larger orders.** A persistent cart and visible total encourage shoppers to add "one more item", raising the average order value.
- **Fewer service problems.** Because the cart enforces real stock, the store avoids overselling, cancellations and the customer-service work that follows.
- **Demand signals for later.** Items placed in carts show what customers want, even before checkout exists. The structure is ready for checkout and saved carts to be added later.

---

## 2. Product Search, Filtering and Sorting

### What changed

The Products page now has a toolbar with:

- **Search** by product name, type, description, colors and tags, e.g. "football", "Davenport", "navy quarter-zip". The search waits until the shopper pauses typing, so it doesn't reload on every keystroke.
- **Filters:**
  - Category, such as hoodies, crewnecks, T-shirts, quarter-zips or jackets.
  - Minimum and maximum price.
  - "In stock only".
  - "Size in stock".
- **Sorting:** Recommended, Name A–Z, Price low to high, Price high to low.
- **A results count,** a **"Clear all filters"** button, and a helpful **empty state** when nothing matches.

All filter choices come from the database: only categories that actually contain products, the real price range and the sizes that exist. Filters and sorting work together, and they are kept in the page address, so the browser's back button, a refresh or a shared link keeps the same results.

### Why it helps the shopper

- **They find what they want quickly** among 102 products, instead of scrolling the whole catalogue. Example: choosing "Hoodies" with a $60 maximum price narrows the list to 2 products.
- **They only see what they can buy.** "Size in stock" and "In stock only" hide products that are unavailable in their size.
- **They can browse the way they think:** by budget (price sorting), by style (category) or by an interest such as a sport, a residential college or a school.
- **No dead ends.** If nothing matches, the page says so and offers a one-click reset.

### Why it helps the business

- **More products get seen.** Good search and filters bring less obvious items, such as specific college or sport designs, in front of the shoppers they suit.
- **Fewer abandoned visits.** Shoppers who can't find something quickly tend to leave; fast filtering keeps them on the site.
- **Consistent answers.** The Products page uses the same search as the chatbot, so a shopper gets the same results whether they browse or ask.
- **Room to grow.** Categories and filters are worked out from the data, so new products appear in the right filters without any website changes.

---

## 3. Conversational Follow-Up and Product Context (Chatbot)

### What changed

The shopping assistant now understands natural follow-up questions without the shopper repeating product names. For every message, it is given structured context:

- **The page being viewed,** including the product on a product page.
- **The products shown in its most recent answer,** numbered in display order with their names, colors and prices.
- **The product currently in focus:** the product page being viewed, or the single product just shown.
- **The logged-in customer** (from the secure login session) and the earlier conversation.

This lets it understand questions like:

| Shopper says | The assistant understands |
| --- | --- |
| "Show me Yale hoodies." → "Which one is cheapest?" | Compares the prices of the hoodies it just showed |
| "Is the second one available in medium?" | The second card shown, then checks its medium stock |
| "What about the blue one?" | The shown product whose colors include blue or navy |
| "Do you have this in pink?" (on a product page) | The product on the screen, then checks its real colors |
| "How much is this?" (with nothing in focus) | Asks a short question instead of guessing |

The assistant always confirms facts (price, colors, sizes, stock) with the database before answering. It never invents a color, size or stock level.

### Why it helps the shopper

- **Chatting feels natural,** like talking to a helpful person at the counter: "this one", "the second one" and "the blue one" just work.
- **Less typing and less frustration.** Long product names like "Brooks Brothers Double Knit Full Zip Hoodie Yale" don't need repeating.
- **Trustworthy answers.** Every price, color and stock figure comes from the live database. If the assistant isn't sure which product is meant, it asks instead of guessing wrong.
- **It works on the product page itself.** While looking at an item, the shopper can simply ask "Do you have this in blue?" or "What sizes do you have?".

### Why it helps the business

- **Better conversion.** Shoppers who get quick, accurate answers to "is it available in my size?" are far more likely to buy.
- **Less staff time.** The assistant handles common size, color, price and stock questions that would otherwise come to store staff by phone or email.
- **Protects the brand.** Because the assistant never makes up stock or colors, the store avoids promising products it doesn't have.
- **Logged-in shoppers pick up where they left off.** Their conversation and product context are saved, which encourages them to come back.

---

## 4. Personalized Product Recommendations (Chatbot)

### What changed

The assistant has a new recommendation tool. It turns a shopper's request into concrete preferences and finds the products in the catalogue that meet them. Preferences can include type, budget, color, size, stock, and words such as a sport, a college or "mom/dad". Examples:

- "I need a Yale sweatshirt under $60."
- "Find me something blue."
- "I'm looking for a hoodie in medium."
- "Show me something under $40."
- "I want a gift for a Yale student."
- "What would you recommend?" (no preferences: a varied selection, one of each kind of item)

Recommendations appear as the same product cards used across the site, each with a short **reason** built only from catalogue facts. For example:

> *Ua Gameday Double Knit Hood — A hooded pullover sweatshirt; $45.00, within your $60.00 budget; in stock in XS, S, M, XXL*

When nothing matches every preference, the assistant says so plainly and suggests which preference to relax, using real counts. For example, it might say how many products there would be with a higher budget.

### Why it helps the shopper

- **Personal shopping help, available any time.** Shoppers who don't know exactly what they want get a short, relevant list instead of the full catalogue.
- **They see why each item fits:** in budget, in their size, in their color. This makes choosing faster and more confident.
- **Honest results.** Every recommendation is real and in stock (unless they ask otherwise), and the reasons only state facts from the catalogue.
- **Smooth path to buying.** Each recommended card has Add to Cart and links to the full product page.

### Why it helps the business

- **Turns browsers into buyers.** Undecided visitors, such as parents, visitors and gift buyers, get guided to suitable products instead of leaving.
- **Sells across the range.** Recommendations bring forward items a shopper might not have searched for, e.g. a $45 hoodie for a budget-conscious student.
- **Uses inventory well.** Only in-stock products are recommended by default, so demand goes to items the store can actually sell.
- **Insight into customers.** The preferences shoppers state, such as budgets, colors and sizes, show what customers are looking for, which helps future buying decisions.

---

## How the four improvements work together

Together the improvements form one shopping journey, tested end to end:

1. A shopper asks the chatbot: **"I need a Yale hoodie under $60."**
2. The assistant **recommends** two hoodies as product cards, each with a reason: $45.00, within the budget, and the sizes in stock.
3. The shopper clicks a card and lands on the **product page**.
4. They choose **size M** and click **Add to Cart**. The cart count in the navigation bar updates.
5. Still on the product page, they ask: **"Do you have this in blue?"**
6. The assistant knows **"this"** is the hoodie on screen. It checks the database and answers: navy and white, so yes, navy is the blue option, in stock in XS, S, M and XXL.
7. Later, they use **search and filters** on the Products page to find something else, add it, and review everything on the **cart page** with an accurate total.

For the **shopper**, the site now helps at every step: finding, deciding, asking and collecting. For the **business**, each step makes a sale more likely, while keeping every price, size and stock figure accurate, because it all comes from the store's single product database.
