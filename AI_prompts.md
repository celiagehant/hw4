# Homework 4 — AI Prompts

A record of the prompts used for Homework 4.

## Problem 2

Create output/harness.md and paste this text: The data base contains the following information:
Catalogue: The catalogue table lists every product the shop sells. Each product has a unique product_id, a name, a garment_type (hoodie, crewneck, T-shirt, cap, etc), a written description, its colors, a photo and its price. This is important for the chatbot because it can find and describe the right products when a customer asks for something like "a navy hoodie."

Inventory: The inventory table tracks stock. Each row links a product_id to one size (XS to XXL) and the quantity available. id is the row's identifier. This is important because it lets the shop and chatbot tell customers whether an item is available in their size before they try to buy it.

Users: The users table stores registered customers. It holds an id, the full name, a unique email, a securely hashed password_hash and the account's created_at date. This is important because it lets customers log in so the chatbot can recognize them and keep their conversation history.

## Problem 3

1. Frontend
Build Campus Customs website using React, Vite, and TypeScript. Create a top navigation bar with working navigation links to: Home, Products, About Us, Long In, Create Account. Each should have its own route/page.
2. Home page
Create a simple, professional Campus Customs home page with the title "Welcome to Campus Customs". 
Include a clear call-to-action directing users to browse the Products page.
3. About Us page
Use this text:
"We sell official licensed merchandise from Yale University, offering everything you need to become a true Yalie! If you are a student, staff, family member or just a visitor, we have you covered. You can visit us in our store at 57 Broadway, New Haven, CT 06511, or order online through our website."
Present this in a clean, professional layout.
4. Products page
The Products page must load products from the existing catalogue/database through the backend API.
For each product, display:

* Product image using the image path from the data folder.
* Product name
* Price
* Short description

Display the products as clickable cards in a clean grid.
5. Product detail page
Clicking a product card must navigate to a unique product-detail page for that product.
The product detail page should have:

* A large product image
* Product name
* Full product description/text
* Price
* Sizes, variants, and/or stock information when that information exists in the catalogue/database

Use the product ID or another reliable unique identifier for routing rather than relying only on the product name.
6. Login and Create Account pages
Create simple placeholder pages for:

* Log in
* Create Account

Authentication does not need to be implemented for this problem. The pages just need to exist and be reachable from the navigation bar.
7. Chat interface
Add a floating chat interface in the bottom-right corner of the website.
It should:

* Be visible from the main website
* Open into a small chat panel when clicked
* Have a text input and send button
* Look like a real chatbot interface

The chatbot does NOT need to communicate with an agent yet. A frontend stub/mock interface is sufficient, but structure it so that it can later call the backend agent.
8. Backend
Create:
`backend/main.py`
Use FastAPI.
The backend should provide a simple API that allows the React frontend to retrieve the products from the existing database/catalogue.
At minimum, create an endpoint to return the product data needed by the Products and Product Detail pages.
Also configure the backend so that the existing product images can be served to the frontend using their existing image paths.

Do not spend excessive time on visual polish because we will do that later.

## Problem 4

1. Create Account
Build a normal Create Account page/form with the following required fields:

* First name
* Last name
* Email
* Password
* Confirm password

The user should have to enter the password twice, and the application should verify that the two passwords match before creating the account.
Validate the form appropriately, including:

* All required fields are completed.
* Email has a valid format.
* Password and confirmation password match.
* Email cannot be registered more than once.

When the account is successfully created, store the new user in the existing `users` table.
2. Password security
Passwords must NEVER be stored as plaintext in the database.
Use a secure, industry-standard password hashing method such as bcrypt or Argon2. Store only the password hash in the database, never the original password.
When a user logs in, securely verify the entered password against the stored password hash.
Do not expose passwords or password hashes through API responses, frontend code, logs, or error messages.
3. Login
Build a normal Login page/form with only:

* Email
* Password

The login should check the provided credentials against the existing `users` table.
A valid user should be able to log in successfully, while incorrect credentials should produce an appropriate error message without revealing whether the email or password was specifically incorrect.
Show me the results so i can make tests.

Update `output/harness.md` with a clear description of how authentication works, including:

* What information is stored for each user.
* How passwords are protected.
* How registration works.
* How login verifies passwords.
* Which API endpoints are used for authentication.

Do NOT include any actual passwords or password hashes in the documentation.

## Problem 5

1. Required backend structure
Create these four agent files:

* `backend/prompts/prompt.md` — system prompt
* `backend/agent.py` — PydanticAI agent entry point and wiring
* `backend/tools.py` — tools that the agent can call
* `backend/models.py` — Pydantic/PydanticAI structured types

2. PydanticAI agent
Implement a PydanticAI agent for the Campus Customs shop chatbot.
The agent should:

* Load its system instructions from `backend/prompts/prompt.md`.
* Use the course-required AI model through Portkey.
* Be properly initialized/wired in `backend/agent.py`.
* Return a structured response using the Pydantic models defined in `backend/models.py`.
* Be callable from the FastAPI application.

3. System prompt
In`backend/prompts/prompt.md` include the Campus Customs chatbot's basic:

* Brand/store identity
* Friendly and helpful Campus Customs voice
* Role as a Yale merchandise shopping assistant
* Basic safety/behavior instructions
* Instructions to avoid making up product information when the necessary information is not available

4. Agent tools
In:`backend/tools.py` implement the tools needed for the chatbot to interact with the existing Campus Customs data where appropriate. The chatbot should retrieve/use product information from the existing catalogue/database. Do not create duplicate product data if the existing database/catalogue already contains the information.
Properly register/wire the tools with the PydanticAI agent in `agent.py`. 
5. Structured models
In:`backend/models.py` define appropriate PydanticAI structured types for the chatbot response.
Include types for chat replies and product cards as needed, for example:

* Chat response text
* Product information/card data
* Product name
* Price
* Image/path when available
* Product ID when available

Use the existing product/catalogue structure rather than inventing incompatible fields.
6. FastAPI chat endpoint
In:`backend/main.py` expose a chat API endpoint that accepts a message from the website and returns the agent's response.
The flow should be:
Frontend chat widget → FastAPI chat endpoint → PydanticAI agent → course model via Portkey → structured response → frontend chat widget.
Make sure the endpoint can handle normal user messages and return an appropriate response to the frontend.

7. Connect the frontend chat widget
Update the existing floating chat interface so that it is no longer just a mock.
When the user sends a message:

1. The frontend sends the message to the FastAPI chat endpoint.
2. FastAPI passes it to the PydanticAI agent.
3. The agent generates a response using the course model through Portkey.
4. The response is returned to the frontend.
5. The chat widget displays the response.

Include a loading state while waiting for the agent and a reasonable error message if the API call fails.
Do not redesign the entire website; integrate with the existing Campus Customs chat.
8. Environment variables and secrets
Use environment variables for API keys and configuration.
Do NOT hardcode:

* Portkey API keys
* Model API keys
* Other credentials or secrets

Check the existing project configuration and follow the same approach.
9. Harness documentation
Update:`output/harness.md`and add:

* How the frontend communicates with FastAPI.
* The chat endpoint and what it accepts/returns.
* How the PydanticAI agent is loaded.
* How `prompt.md` is loaded as the system prompt.
* Which model/provider is used through Portkey.
* How the agent's tools are connected.
* How the structured response models in `models.py` are used.

Do not include any API keys or secrets in the documentation. Keep the previous information in the file.

run uvicorn main:app --reload --port 8000

## Problem 6

1. Product information tools
Define and register the tools necessary for the PydanticAI agent to look up real information from:
`campus_customs.db`
The agent must be able to retrieve:

* Product description
* Product price
* Product stock quantity
* Stock quantity for a specific size when the customer asks about a particular size

Use the actual SQLite database as the source of truth. Do NOT hardcode product prices, descriptions, or inventory quantities in the tools or prompt.
The tools must be properly registered with the PydanticAI agent so the agent can actually call them.
2. Accurate inventory and pricing
The agent must NEVER invent:

* Prices
* Stock quantities
* Product descriptions
* Available sizes

If the requested information is not present in the database, the agent should clearly tell the customer that the information is unavailable rather than guessing.
If a requested size is out of stock, the agent must clearly state that the size is out of stock.
If a product does not exist in the database, the agent should clearly say that it could not find the product rather than making up an answer.
3. Agent instructions
Expand:
`backend/prompts/prompt.md`
so the system prompt explicitly instructs the agent to use the database tools whenever a customer asks about:

* Product price
* Product description
* Stock
* Stock by size
* Product availability

The prompt should make clear that the database is the source of truth and that the agent must not guess or invent product information.
4. Structured return types
Update the Pydantic structured types in:
`backend/models.py`
Create appropriate return types for the tool lookup results.
Include the fields that are actually useful for the agent, such as:

* Product ID
* Product name
* Description
* Price
* Size, when relevant
* Stock quantity, when relevant
* Availability/status, when useful

Use appropriate optional fields where a value may not exist.
Make sure the tool return types are actually used by the tools and agent rather than defining unused models.
5. Harness documentation
Update:
`output/harness.md`
List every tool created in this part and explain:

* The tool's name.
* What question/information it handles.
* What database information it looks up.
* Which model fields the tool returns.
* Why those fields were chosen.
* How the tool handles missing information.
* How the tool handles out-of-stock sizes.

Do not erase what was in the file, only update.

## Problem 7

1. Chat product search
Add a search/category capability to the chatbot.
When a customer asks the chatbot for a type or category of product, for example:

* "What hoodies do you have?"
* "Show me Yale shirts."
* "Do you have mugs?"
* "What sweatshirts are available?"

the agent should use an appropriate tool to search the existing Campus Customs catalogue/database and return the matching products. Do not invent products, prices, descriptions, images, or other product information.
2. Structured product matches
The agent must return product search results as structured data, not just mention the products in plain text.
Each product match should contain the information needed by the frontend to render a product card, including:

* Product ID / unique identifier
* Product name
* Image/path
* Price
* Short product information/description

Use or update the Pydantic structured types in:
`backend/models.py`
Make the structure clear and consistent so the frontend knows exactly how to interpret the agent's product matches.
If there are no matching products, the agent should clearly communicate that no matching products were found and should return an empty product-match list rather than inventing results.
3. API contract
Maintain a clear API contract between the backend agent and frontend.
The flow should be:
Customer message
→ Frontend chat widget
→ FastAPI chat endpoint
→ PydanticAI agent
→ Product search tool
→ Structured product matches
→ FastAPI response
→ Frontend
→ Product cards rendered on the page
Make sure the chat response can contain both:

* The agent's natural-language reply.
* A structured list of matching products when the agent performs a product search.

4. Frontend rendering
Update the existing frontend chat functionality so that when the backend returns structured product matches, the website dynamically renders them as product cards.
Each dynamically rendered card should show:

* Product image
* Product name
* Price
* Short product information

The cards should fit naturally into the existing Campus Customs website design.
The product cards should be rendered on the website as part of the response to the chat search.
5. Prompt update
Update:
`backend/prompts/prompt.md`
Clearly instruct the agent that when a customer asks to see/search for a category or type of product, it should use the product-search tool and return structured product matches for the frontend.
The prompt should also instruct the agent to:

* Use real catalogue/database information.
* Never invent products or product information.
* Return structured matches when appropriate.
* Return no matches when nothing relevant is found.

7. Harness documentation
Update:
`output/harness.md`
Clearly document the complete flow of search results from the customer message to the webpage.
Explain:

1. How the user asks for a product/category through chat.
2. Which agent tool performs the search.
3. What structured data the agent returns.
4. What fields are included in each product match and why.
5. How the FastAPI response passes the structured matches to the frontend.
6. How the frontend renders the matches as product cards.
7. How clicking a dynamically generated card uses the existing product-detail route.

Make the API contract between backend and frontend explicit.

## Problem 8

1. Persistent chat history for logged-in users
When a user is logged in, save their chat history in the existing database.
Create an appropriate database table for chat history if one does not already exist.
Each stored chat message should be associated with the correct logged-in user. The history should preserve enough information to reconstruct the conversation, including at minimum:

* User/customer identifier
* Message/role (user or assistant)
* Message content
* Appropriate timestamp

Use the existing authenticated user's ID as the reliable association between the conversation and the customer. Do not associate history only by name or email.
A user's chat history must be private to that user. Do not return another customer's conversation history.
2. Reload chat history
When a logged-in customer returns to the website and opens the chatbot, retrieve their previous chat history from the database and display it in the chat interface.
The agent should also have access to the relevant previous conversation history so that it can maintain conversational context.
Make sure the history is loaded for the correct authenticated user.
If there is no previous history, start with an empty conversation.
3. Guest users
Customers who are NOT logged in must still be able to use the chatbot.
Guest users should be able to have a normal conversation during their current session, but their chat history does NOT need to be persisted in the database.
Do not require login just to use the chatbot.
Do not create fake user records for guests simply to store their chat history.
4. Customer identity in agent context
The PydanticAI agent must know who is chatting when the customer is logged in.
Pass the authenticated customer's information into the agent using PydanticAI dependencies (`deps`) or another equally clear and structured pattern.
At minimum, make the following customer fields available to the agent:

* Customer/user ID
* First name
* Last name
* Email

Use the authenticated session/user information as the source of truth.
The agent should be able to use the customer's name naturally when appropriate, but it should not expose private customer information unnecessarily.
For guests, clearly represent that there is no authenticated customer rather than inventing an identity.
5. Page context
Add page context to the agent request so the agent knows what page/product the customer is currently viewing.
This is especially important on individual product pages.
For example, if the customer is viewing a specific product and asks:
"Do you have this in pink?"
the agent should understand that "this" refers to the product currently displayed on the page.
Pass enough structured context for the agent to identify the current page and, when applicable, the current product.
For a product page, include useful context such as:

* Page type
* Product ID
* Product name
* Product information relevant to the conversation
* Any other information needed to resolve references such as "this", "this one", or "the product I'm looking at"

Do not rely on the agent guessing which product the user means from the conversation alone.
6. Frontend → backend → agent context
Update the chat request flow so that the necessary context is passed from the frontend to FastAPI and then into the PydanticAI agent.
The overall flow should be:
Frontend
→ authenticated user information/session + page context + chat message
→ FastAPI
→ agent dependencies/context
→ PydanticAI agent
→ tools/database when needed
→ response
→ frontend
7. Conversation history and agent calls
Make sure the agent receives the appropriate previous conversation history when a logged-in customer continues an existing conversation.
Avoid duplicating messages when saving/reloading history.
Ensure that guest conversations work without requiring database persistence.
If the existing PydanticAI implementation has a message/history mechanism, integrate the database-backed history cleanly with it rather than creating a second unrelated conversation system.
8. Prompt update
Update:
`backend/prompts/prompt.md`
Add instructions explaining that:

* The agent may receive authenticated customer information.
* The agent may receive page/product context.
* References such as "this", "this product", or "this one" should be resolved using the current page context when available.
* The agent should use the customer's name naturally when appropriate.
* The agent must not invent customer identity or product context.
* Guests do not have persistent chat history.

Do not put actual customer data into the system prompt. Customer-specific information should be passed dynamically through the agent context/dependencies.
9. Harness documentation
Update:
`output/harness.md`
Clearly document:
Chat history

* The database table used to store chat history.
* The fields stored for each message.
* How messages are associated with a customer.
* How history is loaded when a logged-in customer returns.
* How guest conversations differ from logged-in conversations.

Customer information

* Which customer fields the agent receives.
* How the information is passed to the agent.
* How authentication is used to determine the customer.

Page context

* What page context is passed to the agent.
* How product context is represented.
* How the context allows the agent to understand questions such as "do you have this in pink?"

Explain the complete flow from the webpage to the agent.

## Problem 9

Implement the following FOUR usability improvements:
1. FRONT-END: Shopping Cart
Add a complete shopping-cart experience to the existing Campus Customs website.
Requirements:

* Add an "Add to Cart" button to product cards and the product detail page.
* If a product has sizes, require the customer to select a size before adding it to the cart.
* If a product does not have sizes, allow it to be added directly.
* Do not allow customers to add quantities greater than the available stock.
* Reuse the existing product/database information for price, size, availability, and images. Do not hardcode product information.
* Add a cart icon/link to the main navigation bar.
* Display the number of items currently in the cart.
* Create a cart page or appropriate cart panel showing:
   * Product image
   * Product name
   * Selected size when applicable
   * Unit price
   * Quantity
   * Remove item functionality
   * Quantity controls
   * Total price
* Recalculate totals whenever quantities change.
* Prevent a customer from increasing quantity beyond available inventory.
* Provide a clear empty-cart state.
* Make the cart usable on both product pages and product cards.
* Preserve the existing product-detail-page routing.
* Keep the implementation consistent with the existing React/Vite/TypeScript architecture.

Cart persistence:

* At minimum, preserve the cart while the user navigates around the site and refreshes the page during the current session.
* If there is already an appropriate authenticated-user persistence pattern in the backend, you may persist the cart for logged-in users, but do not introduce unnecessary complexity if it would risk breaking existing authentication/chat functionality.
* Guests must be able to use the cart.

2. FRONT-END: Product Search, Filtering, and Sorting
Improve the Products page so customers can more easily find products.
Add:
Search
A search input that lets the user search existing catalogue products by relevant text such as:

* Product name
* Product type/category
* Description

Filters
Where the underlying data supports them, allow filtering by:

* Product type/category
* Price range
* Availability
* Size

Do not invent filter values. Derive available categories, sizes, prices, and availability from the existing catalogue/database.
Sorting
Add sorting options such as:

* Recommended/default
* Name A–Z
* Price: low to high
* Price: high to low

Requirements:

* Filtering and sorting should work together.
* Make it easy to clear/reset all filters.
* Show a useful empty state when no products match.
* Keep product cards consistent with the existing P3/P7 design.
* Clicking a product must continue to use the existing product-detail route.
* Do not duplicate product data in the frontend.
* Prefer using the existing backend/product API where appropriate rather than creating a second source of truth.

If practical, debounce the search input so it does not unnecessarily trigger an API request for every keystroke.
3. AGENT/BACKEND: Conversational Follow-Up and Product Context
Improve the Campus Customs chatbot so it can understand natural follow-up questions instead of requiring the customer to repeat the product name.
Build on the page-context functionality implemented earlier.
The agent should understand references such as:

* "Do you have this in pink?"
* "How much is this?"
* "What sizes do you have?"
* "Is the second one available in medium?"
* "What about the blue one?"
* "How much is that one?"
* "Does it have any other colors?"

For example:
Customer:
"Show me Yale hoodies."
Agent:
[structured hoodie product cards]
Customer:
"Do you have this in pink?"
The agent should understand what "this" refers to using available page/product/search context and then use the appropriate database tool to determine whether that product/variant actually exists and is in stock.
Similarly:
Customer:
"Which one is cheapest?"
The agent should understand that "which one" refers to the products in the relevant recent search results.
Implement this using structured context rather than relying only on the natural-language conversation.
The agent context should be able to contain, where available:

* Current page type
* Current product ID
* Current product name
* Current product information
* Last product-search results
* Product IDs/names returned in the most recent structured product-card response
* Relevant selected product
* Authenticated customer identity from P8
* Relevant conversation history from P8

Use PydanticAI dependencies or the existing equivalent dependency/context mechanism.
Important:

* Do NOT trust arbitrary customer identity information sent by the frontend. Continue using the authenticated user as the source of truth.
* Do NOT guess what "this" means when there is insufficient context. Ask a concise clarification question instead.
* Do NOT invent product colors, prices, sizes, or inventory.
* When a follow-up requires factual product information, call the appropriate existing database/product tool.
* Reuse the existing tools whenever possible instead of creating duplicate database logic.
* Reuse the existing structured product-search functionality.

Update `backend/prompts/prompt.md` so the agent explicitly knows how to:

* Use page context.
* Use recent product-search results.
* Resolve references such as "this," "that," "the first one," and "the second one."
* Ask for clarification when the reference cannot be resolved.
* Use tools for factual product information.
* Never invent inventory, prices, sizes, or product attributes.

Update `backend/models.py` if necessary to represent this context cleanly.
4. AGENT/BACKEND: Personalized Product Recommendations
Add a recommendation capability to the Campus Customs agent.
Create an appropriate tool in `backend/tools.py`, such as `recommend_products`, that searches the existing catalogue/database and returns products matching the customer's request.
The agent should be able to handle requests such as:

* "I need a Yale sweatshirt under $60."
* "Find me something blue."
* "I want a gift for a Yale student."
* "Show me something under $40."
* "I'm looking for a hoodie in medium."
* "What would you recommend?"

The recommendation functionality should:

1. Understand relevant customer preferences from the request, such as:
   * Product type
   * Price/budget
   * Color
   * Size
   * Availability
   * Other attributes actually present in the catalogue
2. Query the existing product database/catalogue.
3. Return structured product matches rather than making the agent write product information manually.
4. Reuse the existing P7 product-card structure so recommendations can be rendered by the existing frontend.
5. Include a short structured "reason" or "match explanation" when appropriate, explaining why the product matches the customer's request.

For example, a structured recommendation could contain:

* Product ID
* Product name
* Image/path
* Price
* Short description
* Match/recommendation reason

Do not invent a reason based on information that is not actually available in the catalogue.
If no products match, the agent should clearly say that it could not find a matching product and, where useful, suggest relaxing one of the constraints.
The recommendation tool must use the existing database/catalogue as its source of truth.
Do not create a second product database.
Integration Requirements
Make sure all four improvements work together.
For example:
Customer:
"I need a Yale hoodie under $60."
The agent should be able to return structured recommendations.
The frontend should render the products using the existing product-card component.
The customer should be able to click a recommended product and reach the existing product detail page.
From the product page, the customer should be able to select a size and add it to the cart.
The customer can then ask:
"Do you have this in blue?"
The agent should use the current product/page context and existing database tools to answer accurately.

Write output/usability.md to explain the 4 usability improvements and why it helps the shopper and the business.

## Problem 10

Transform the existing Campus Customs website into a polished, imaginative, and distinctive storefront experience. The goal is to make the website feel like a real, premium Yale merchandise brand rather than a basic student project.
Overall Creative Direction
Create a visual identity that combines:

* Yale heritage
* Premium collegiate retail
* Modern e-commerce
* A subtle playful personality
* Strong visual hierarchy
* Smooth, intentional motion
* An engaging AI shopping assistant

Keep Yale's recognizable color palette as the foundation, especially Yale blue, but do NOT make every element blue.
The site should feel sophisticated and modern, with Yale blue used strategically for branding, buttons, accents, navigation, and interactive states.
Use white/cream/light neutral backgrounds and restrained accent colors to create contrast.
The design should feel inspired by a premium university bookstore or lifestyle brand, not by a generic SaaS dashboard.
1. Typography and Font System
Create a deliberate typography hierarchy.
Use a combination of:

* A sophisticated serif/display font for major storefront headlines and editorial moments.
* A clean modern sans-serif for navigation, product information, prices, buttons, and UI.

The combination should evoke:
"Yale tradition + modern fashion/e-commerce."
Establish clear hierarchy between:

* Brand/store name
* Hero headline
* Section headings
* Product names
* Prices
* Descriptions
* Navigation
* Buttons
* Chat messages
* Supporting information

Do not use too many fonts.
Typography should make the website feel intentionally designed rather than like default browser text.
Use appropriate font weights, letter spacing, and line heights.
2. Color System
Keep Yale blue as the core brand color.
Create a small, consistent design system around it:

* Yale blue for primary branding and important actions.
* White / warm off-white for major backgrounds.
* Dark navy/charcoal for text.
* Subtle neutral grays for secondary information.
* One restrained accent color for occasional highlights.

Do NOT turn the entire website into a blue background.
Use color strategically to create hierarchy.
For example:

* Yale blue CTA buttons
* Yale blue hover states
* Yale blue navigation accents
* Neutral product cards
* Subtle blue background sections
* Accent color for small promotional or interactive moments

Make sure contrast and accessibility remain strong.
3. Navigation / Header
Redesign the navigation bar so it feels like a premium storefront.
Keep the existing navigation functionality:

* Home
* Products
* About Us
* Login/Create Account
* Cart

But improve the visual hierarchy.
Consider:

* A more distinctive Campus Customs wordmark/logo treatment.
* A clean, elegant header.
* Subtle separation from the page.
* A visible cart indicator.
* A clear account state when logged in.
* Smooth hover/active states.

The navigation should feel lightweight and premium rather than like a standard Bootstrap navbar.
On scroll, consider a subtle sticky-header transformation such as:

* Slightly reduced height
* Background blur/transparency
* Subtle shadow or border

4. Homepage / Hero
Make the homepage feel like the entrance to an actual storefront.
Create a strong hero section with a memorable visual composition.
Possible direction:
"YOUR YALE. YOUR STYLE."
or another short, sophisticated Campus Customs tagline.
The hero should communicate that Campus Customs sells official Yale merchandise.
Include a strong CTA such as:
"Shop the Collection"
and optionally:
"Ask our AI stylist"
Do not overcrowd the hero with text.
Create strong visual contrast between the hero and the product sections below it.
Use product imagery from the existing catalogue whenever possible.
5. Editorial Product Presentation
Make product presentation a major part of the design.
Instead of displaying every product as a basic rectangular card, create a more editorial e-commerce layout.
Product cards should have:

* Large, high-quality product image
* Product name
* Price
* Short description where appropriate
* Availability/size information where useful
* Add to Cart interaction
* Subtle hover interaction

Use whitespace intentionally.
Consider varying visual scale or layout for featured products so the page feels curated rather than like a database table.
For example:
FEATURED COLLECTION
[Large featured product] [Two smaller products]
then:
SHOP ALL
[Product grid]
Do not overdo masonry layouts if they make product comparison difficult.
6. Product Card Motion
Add tasteful micro-interactions.
Examples:

* Product image subtly zooms on hover.
* Card lifts slightly.
* Add-to-cart button appears or becomes more prominent.
* Image transitions smoothly between states.
* Price/availability remains stable and readable.
* Clicking the card feels responsive.

Use CSS transitions or a lightweight animation library already present in the project.
Do NOT add excessive bouncing, spinning, or distracting animations.
The motion should feel:
"premium retail"
not:
"video game."
7. Product Detail Pages
Make individual product pages feel like a premium shopping experience.
Use a strong two-column layout on desktop:
LEFT:
Large product imagery.
RIGHT:

* Product name
* Price
* Description
* Size selector
* Stock information
* Quantity
* Add to Cart
* Relevant product information

Create clear visual hierarchy.
The selected size should have an obvious active state.
The Add to Cart CTA should be visually prominent.
Add subtle transitions when changing size or quantity.
On mobile, stack the sections naturally.
8. Yale / Handsome Dan Moment
Introduce Handsome Dan (Yale's mascot). Give the chatbot a small Handsome Dan-inspired avatar/icon and make the assistant feel like a Yale shopping companion.
9. Chatbot Design
The chatbot should feel like part of the storefront, not a generic customer-service widget.
Redesign the existing floating chat panel.
Give it:

* A distinctive Yale/Campus Customs identity.
* A polished header.
* A small assistant avatar.
* Friendly welcome message.
* Suggested prompts.
* Product cards integrated naturally into conversations.
* Typing/loading animation.
* Clear distinction between user and assistant messages.
* Smooth opening/closing animation.

For the welcome state, provide useful suggested questions such as:
"Find me a Yale hoodie"
"What's under $50?"
"Help me find a gift"
"Show me what's available in medium"
Make the chatbot feel like a personal shopping assistant rather than a technical AI interface.
When the agent returns product cards, make those cards feel native to the conversation.
10. Chat/Product Interaction
Create a strong visual connection between the chatbot and the storefront.
When the agent recommends a product:

* Display the product image.
* Product name.
* Price.
* Short reason/recommendation.
* CTA such as "View Product" or "Add to Cart."

When the user clicks the product, take them to the existing product detail page.
If the user is currently on a product page, the chatbot should visually understand that it is helping with that product.
Do not duplicate product-detail functionality inside the chatbot.
11. Motion Design System
Create a consistent motion language across the website.
Use subtle animation for:

* Page transitions
* Product card hover
* Buttons
* Cart updates
* Chat opening/closing
* Chat messages appearing
* Product recommendations appearing
* Filter changes
* Dropdowns/modals
* Navigation states

Use short, smooth transitions.
Avoid:

* Excessive parallax
* Constant animations
* Bouncing elements
* Distracting background effects
* Animations that slow down shopping

Respect `prefers-reduced-motion` for accessibility.
12. Responsive Design
The design must work well on:

* Desktop
* Tablet
* Mobile

Pay particular attention to:

* Navigation
* Product grids
* Product detail pages
* Cart
* Chatbot
* Typography
* Buttons
* Product images

Do not simply shrink the desktop design.
Create sensible responsive layouts.
14. Accessibility and Usability
Even though the emphasis is visual creativity, usability must remain strong.
Ensure:

* Good color contrast
* Keyboard-accessible buttons
* Visible focus states
* Accessible image alt text
* Clear labels
* Readable font sizes
* Reduced-motion support
* Buttons remain understandable without relying only on color

Do not sacrifice usability for visual effects.

Write output/design.md explaining the previous changes and why it should help customers stick around and buy. Keep it concrete and short.

## Problem 11

Test the LIVE Campus Customs website. Create:`output/app_check.html`
and store all screenshots in:
`output/app_check_images/`
The HTML must link to the screenshots using relative paths, for example:
`app_check_images/inventory.png`
Check 1 — Chat Inventory Lookup
Use the live website's chatbot to ask a realistic product inventory question.
For example:
"How many Yale hoodies do you have in stock?"
or, if the catalogue requires a specific size:
"How many Yale hoodies do you have in medium?"
Use a product that actually exists in the current database/catalogue.
The screenshot must clearly show:

* The user's inventory/stock question.
* The agent's response.
* The relevant product/size if applicable.
* The actual inventory information returned by the agent.

The response should demonstrate that the agent is using the database and providing honest stock/price information rather than inventing a quantity.
Save the screenshot as something clear such as:
`output/app_check_images/inventory.png`
Under the screenshot, include a short 1–2 sentence caption explaining what the screenshot proves.
Check 2 — Dynamic Search-Result Cards
Use the live chatbot to ask a category/product-search question.
For example:
"Show me Yale hoodies."
or another category that definitely exists in the current catalogue.
The screenshot must clearly show:

* The user's category question.
* The agent's response.
* The dynamically generated product cards.
* Product images.
* Product names.
* Prices and/or relevant product information.

The screenshot should demonstrate that the cards are dynamically returned/rendered from the agent's structured product-search response, rather than being static cards already displayed on the page.
Save the screenshot as:
`output/app_check_images/search_cards.png`
Under the screenshot, include a short 1–2 sentence caption explaining what the screenshot proves.
Check 3 — Problem 9 Usability Feature
Identify one of the usability/design improvements implemented in Problem 9.
Choose the feature that is easiest to demonstrate clearly and that provides the strongest visual evidence.
Examples include:

* Shopping cart
* Product search/filtering/sorting
* Conversational follow-up/product context
* Personalized product recommendations
* Storefront/design improvements

Actually use the live website to demonstrate the feature.
Do not take a generic screenshot of the homepage if it does not clearly demonstrate the feature.
The screenshot should show the user interacting with the feature and the resulting behavior.
Save the screenshot with a descriptive filename, for example:
`output/app_check_images/p9_usability.png`
Under the screenshot, include a short 1–2 sentence caption explaining exactly what the screenshot proves.
app_check.html 
Make `output/app_check.html` extremely easy for a grader to evaluate.
Use a clean structure such as:
Campus Customs — Problem 11 App Check
A short introductory sentence explaining that the page documents live-site tests.
1. Inventory Chat Lookup
[Inventory screenshot]
Caption explaining what it proves.
2. Dynamic Search-Result Cards
[Search cards screenshot]
Caption explaining what it proves.
3. Problem 9 Usability Feature
[Usability screenshot]
Caption explaining what it proves.
Each section must contain:

1. A clear heading.
2. The corresponding screenshot.
3. A concise 1–2 sentence explanation of what the screenshot demonstrates.

Do not combine multiple checks into one screenshot if that makes the evidence unclear.
Screenshot Requirements
Use actual screenshots from the live website.
Make sure screenshots are:

* Legible.
* Large enough to see the relevant interaction.
* Focused on the relevant feature.
* Free of unnecessary unrelated windows or applications.
* Clearly associated with the correct section.

If possible, crop screenshots so the relevant chatbot/product/feature is easy to see while preserving enough surrounding context to demonstrate that it is the live Campus Customs website.
Do not create fake screenshots or mock the results.

## Problem 12

1. Append-only agent audit trail
Create:
`output/audit_trail.json`
The file must record agent-loop activity for each run.
Each relevant audit entry should include:

* `time` — timestamp of the event
* `tool` — tool name used, when applicable
* `args` — short/safe summary of the tool arguments
* `result` — short/safe summary of the tool result
* `stop_reason` — why the agent loop stopped, when the run ends

The audit trail must be APPEND-ONLY, preserve all previous entries.
The audit trail must NOT expose sensitive information.
Never write to the audit trail:

* Passwords
* Password hashes
* Authentication tokens
* API keys
* Secrets/environment variables
* Full private chat messages unnecessarily
* Sensitive personal information unnecessarily

2. Safety rules
Update the existing:`prompts/prompt.md`to include safety rules such as:
Privacy

* Do not reveal private customer information.
* Do not expose information from one customer's account or chat history to another customer.
* Treat customer chat content as private.
* Only use authenticated customer information for the current authenticated customer.
* Do not disclose previous customers' conversations.

Authentication and passwords

* Never reveal passwords.
* Never reveal password hashes.
* Never ask users to provide passwords unnecessarily.
* Never expose authentication tokens, API keys, or environment variables.
* Do not include secrets in agent responses or audit logs.

Image safety / purpose
The product images available to the system should only be used for their intended Campus Customs functionality.
Do not use, repurpose, or expose images for unrelated purposes.
Do not infer sensitive personal characteristics from customer images or use images for purposes unrelated to the exercise.
Only use images as necessary for legitimate product identification, product presentation, or the specific image-related functionality implemented in this project.
Product information

* Use database/catalogue tools for factual product information.
* Never invent prices, inventory, sizes, colors, descriptions, or availability.
* If information is unavailable, say so clearly.
* Do not claim an item is available when the database does not support that claim.

Tool use

* Only use tools for their intended purpose.
* Do not expose internal tool implementation details unnecessarily.
* Do not execute actions outside the capabilities of the application.
* Do not fabricate tool results.

Customer identity

* Use authenticated identity information supplied by the application's trusted authentication mechanism.
* Do not trust a user-provided name/email as proof of identity.
* Do not reveal another customer's information.

Agent behavior

* Be helpful and concise.
* Ask for clarification when the request is ambiguous.
* Do not guess when important information is missing.
* Refuse or redirect requests that would violate the application's privacy or safety rules.

3. Model
Update:`output/harness.md`to add the remaining details so it has all the details to explain the system overview, model fields in model.py and why you chose them, tools and abilities, safety rules and specs (loop limits, result caps, models and how to run the front and end back). 
Do not eliminate what is already written, only update.
