"""Brand Transformation — knowledge base.

Structured, prompt-injectable research on how mediocre businesses become
category references: FOMO / desire mechanics, the origin playbooks of
iconic brands, and the strategy frameworks the specialist agents apply.

Everything here is DATA, injected verbatim into agent prompts so the LLM
reasons from concrete patterns instead of generic marketing platitudes.
Keep entries terse, causal, and example-anchored.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. FOMO / DESIRE MECHANICS
#    Each lever: how it manufactures "I must be part of this", the failure
#    mode when faked, and the brands that ran it well.
# ---------------------------------------------------------------------------

FOMO_LEVERS: dict[str, dict] = {
    "artificial_scarcity": {
        "mechanism": "Cap supply below demand on purpose. Drops, limited runs, "
        "waitlists, numbered editions. Scarcity signals value and forces a decision now.",
        "tactics": [
            "Timed drops with hard sellout (Supreme weekly Thursday drop)",
            "Numbered / serialized units ('1 of 500')",
            "Waitlist with visible queue position (Robinhood, Superhuman, Clubhouse)",
            "Seasonal 'never coming back' framing (McDonald's McRib, Starbucks PSL)",
        ],
        "failure_mode": "Fake scarcity that customers can disprove (restocks minutes later) "
        "destroys trust permanently.",
        "cases": ["Supreme", "Hermès Birkin", "Nintendo (Wii/Switch)", "McRib", "Ferrari (build fewer than demand)"],
    },
    "social_proof_velocity": {
        "mechanism": "Show that many people — especially peers and insiders — are already in. "
        "Momentum itself becomes the reason to join.",
        "tactics": [
            "Live counters (users, orders today, people viewing)",
            "UGC volume as the ad (TikTok, GoPro, Airbnb)",
            "Ratings/reviews front-and-center before price",
            "'Join 2M+ founders' specificity over vague 'thousands'",
        ],
        "failure_mode": "Round, unverifiable numbers read as marketing and lower trust.",
        "cases": ["Amazon reviews", "Booking.com urgency UI", "Notion templates gallery", "GoPro"],
    },
    "exclusivity_and_status": {
        "mechanism": "Membership as identity. The product is a badge that says something "
        "about who you are to a group whose opinion you care about.",
        "tactics": [
            "Invite-only onboarding (Gmail 2004, Clubhouse, Pinterest early)",
            "Tiered access / velvet rope (Amex Black, Soho House)",
            "Owning the object is the flex (Rolex, Gucci, Off-White)",
            "Members-only language, rituals, symbols",
        ],
        "failure_mode": "Exclusivity with nothing behind the door — churns the moment it opens.",
        "cases": ["American Express Centurion", "Soho House", "Clubhouse", "Nike SNKRS", "Raya"],
    },
    "identity_and_tribe": {
        "mechanism": "Sell a worldview and an enemy, not a product. Customers buy to declare "
        "allegiance. The brand is a flag.",
        "tactics": [
            "Name the enemy (Apple '1984' vs IBM; Nike vs your own excuses)",
            "Manifesto over feature list (Patagonia 'Don't buy this jacket')",
            "Rituals and vocabulary only insiders use (CrossFit, Peloton, Harley HOG)",
            "Founder as protagonist of a mission (Tesla, Liquid Death, Red Bull)",
        ],
        "failure_mode": "Borrowed values with no operational proof = greenwashing backlash.",
        "cases": ["Patagonia", "Harley-Davidson", "Liquid Death", "Tesla", "CrossFit"],
    },
    "anticipation_and_ritual": {
        "mechanism": "Engineer a wait and a repeated cue. The gap between want and get is where "
        "desire compounds; the ritual re-triggers it on a schedule.",
        "tactics": [
            "Countdown launches / keynote theater (Apple September event)",
            "Recurring drop cadence the audience organizes their week around",
            "Pre-order as a status act months before delivery (Tesla, video games)",
            "Unboxing designed as a ceremony (Apple packaging)",
        ],
        "failure_mode": "Hype with no payoff on delivery day burns the next launch.",
        "cases": ["Apple keynotes", "PlayStation launches", "Glossier drops", "Yeezy"],
    },
    "loss_and_urgency_framing": {
        "mechanism": "People act harder to avoid losing than to gain. Frame the offer as "
        "something being taken away.",
        "tactics": [
            "Deadline with real consequence (cohort closes, price rises)",
            "Grandfather pricing ('lock this in before it goes')",
            "Abandoned-cart 'your size is almost gone'",
            "Founder's-edition perks that never return",
        ],
        "failure_mode": "Perpetual 'ending soon' banners train customers to ignore every deadline.",
        "cases": ["ConvertKit lifetime deals", "course launches (Hormozi, B-School)", "airline seat maps"],
    },
    "velocity_of_novelty": {
        "mechanism": "Constant small newness keeps attention and gives people a reason to check "
        "back and to talk. The feed / shelf is never the same twice.",
        "tactics": [
            "Limited flavors / colorways on a cadence (Oreo, Nike, Spotify Wrapped)",
            "Collabs that borrow another tribe's audience (Supreme x everything, Nike x designers)",
            "Seasonal menu resets (Starbucks, Shake Shack)",
        ],
        "failure_mode": "Novelty with no core identity = forgettable; nothing to be loyal to.",
        "cases": ["Oreo", "Spotify Wrapped", "Nike", "Starbucks seasonal"],
    },
}

# ---------------------------------------------------------------------------
# 2. ICONIC BRAND ORIGIN PLAYBOOKS
#    "simple product -> billions" — the actual lever, not the myth.
# ---------------------------------------------------------------------------

BRAND_ORIGIN_PLAYBOOKS: dict[str, dict] = {
    "McDonald's": {
        "surface_product": "hamburgers",
        "real_engine": "Not food — real estate + a franchised operating system. The Speedee "
        "Service System productized consistency; Kroc's franchise + property model made land the "
        "asset and the burger the customer-acquisition cost.",
        "levers": ["process standardization", "franchise scaling", "predictability as the promise", "site selection moat"],
        "lesson": "Sell a repeatable system, not a product. Own the layer competitors rent.",
    },
    "Coca-Cola": {
        "surface_product": "sugar water",
        "real_engine": "Distribution ubiquity + emotional branding + secret-formula mythology. "
        "'Within an arm's reach of desire' — bottler network put it everywhere; advertising "
        "attached it to happiness, Christmas, belonging.",
        "levers": ["distribution density", "emotional association", "ritual (the pause)", "mystery/heritage"],
        "lesson": "Commodity + total availability + owned emotional occasion = pricing power.",
    },
    "Red Bull": {
        "surface_product": "caffeine + taurine drink",
        "real_engine": "A media company that happens to sell a can. Owns extreme-sports content, "
        "events, teams. The drink funds the content; the content sells the identity ('gives you wings').",
        "levers": ["content as product", "identity/tribe", "event ownership", "premium price as signal"],
        "lesson": "If the category is commoditized, win the culture around it and charge for the badge.",
    },
    "Starbucks": {
        "surface_product": "coffee",
        "real_engine": "The 'third place' between home and work. Sold real estate + ritual + "
        "name-on-the-cup personalization at scale. Premium ambiance repriced a $0.50 commodity to $5.",
        "levers": ["experience design", "daily ritual habit loop", "ubiquity + consistency", "aspirational accessibility"],
        "lesson": "Reprice a commodity by selling the context and the routine, not the liquid.",
    },
    "Nike": {
        "surface_product": "shoes",
        "real_engine": "Sells self-transcendence. Athlete endorsement + 'Just Do It' turned a "
        "sneaker into a personal-achievement narrative. Later: scarcity engine (SNKRS drops) on top.",
        "levers": ["hero/aspiration archetype", "narrative over spec", "scarcity drops", "cultural collabs"],
        "lesson": "Attach the product to who the customer wants to become.",
    },
    "Supreme": {
        "surface_product": "t-shirts / skate gear",
        "real_engine": "Manufactured scarcity + subculture credibility + collab reach. Deliberately "
        "under-produces; weekly drops sell out in seconds; resale market advertises for free.",
        "levers": ["hard scarcity", "subculture authenticity", "drop ritual", "collab borrowing"],
        "lesson": "Constrain supply, own a cadence, let the resale market be your ad budget.",
    },
    "Apple": {
        "surface_product": "computers / phones",
        "real_engine": "Design as identity + closed ecosystem lock-in + keynote theater. Premium "
        "price is the signal; the ecosystem is the moat; the launch is the marketing.",
        "levers": ["design/craft archetype", "anticipation ritual", "ecosystem lock-in", "premium-as-signal"],
        "lesson": "Vertical control + ceremony + taste lets you set price instead of taking it.",
    },
    "Tesla": {
        "surface_product": "electric cars",
        "real_engine": "$0 paid ads. Founder mission narrative + waitlist/pre-order + software-update "
        "novelty + owners as evangelists. Sold the future, delivered updates.",
        "levers": ["mission/founder narrative", "pre-order status", "continuous novelty (OTA)", "owner tribe"],
        "lesson": "A strong enough point of view and a waitlist replaces a marketing budget.",
    },
    "Instagram / TikTok / YouTube": {
        "surface_product": "a feed",
        "real_engine": "Two-sided attention loop: creators chase reach, viewers chase novelty, the "
        "algorithm rewards both. Variable-reward scroll + creator status ladder + network effects.",
        "levers": ["variable reward loop", "creator status economy", "network effects", "low-friction creation"],
        "lesson": "Build a loop where each user's activity increases the value for the next user.",
    },
    "Liquid Death": {
        "surface_product": "canned water",
        "real_engine": "Comedy + heavy-metal identity in the most boring category. 'Murder your "
        "thirst.' The brand voice is the product; water is the medium.",
        "levers": ["identity/tribe", "category contrast", "shareable voice", "merch as media"],
        "lesson": "In a commodity, an extreme distinctive voice is the differentiation.",
    },
    "Decathlon": {
        "surface_product": "sports gear",
        "real_engine": "Vertical integration + own-brands (Quechua, Domyos...) + big-box price "
        "leadership. Owns design->manufacture->retail, so quality-per-dollar is unmatched.",
        "levers": ["vertical integration", "private-label portfolio", "price leadership", "accessibility"],
        "lesson": "Owning the whole chain lets you win on value where others margin-stack.",
    },
    "Gucci / Versace (luxury)": {
        "surface_product": "clothes / bags",
        "real_engine": "Artificial scarcity + heritage story + price-as-status + creative-director "
        "reinventions that generate press cycles. Never discount; destroy unsold stock.",
        "levers": ["price-as-signal", "heritage narrative", "controlled scarcity", "designer news cycle"],
        "lesson": "Protecting price and scarcity IS the product for status goods.",
    },
}

# ---------------------------------------------------------------------------
# 3. STRATEGY FRAMEWORKS  (agents cite these by name in their reasoning)
# ---------------------------------------------------------------------------

FRAMEWORKS: dict[str, str] = {
    "jung_brand_archetypes": (
        "12 archetypes: Innocent, Explorer, Sage, Hero, Outlaw, Magician, Everyman/Regular Guy, "
        "Lover, Jester, Caregiver, Creator, Ruler. Pick ONE primary as the brand's personality core; "
        "it dictates voice, story, and visual mood. (Hero=Nike, Outlaw=Harley/Liquid Death, "
        "Ruler=Mercedes, Magician=Apple/Disney, Everyman=IKEA, Jester=Old Spice.)"
    ),
    "category_design_playbigger": (
        "Don't compete in a category — design a new one you can be #1 in. Define the problem the "
        "market didn't know it had, name it, evangelize the frame. Category king takes ~76% of the "
        "category's economics. Steps: point of view -> name the category -> lightning-strike launch -> "
        "condition the market -> mobilize the company around it."
    ),
    "dunford_positioning": (
        "Positioning = context. 5 components: (1) competitive alternatives (what customers would do "
        "otherwise), (2) unique attributes you have that they don't, (3) the value those attributes "
        "enable, (4) the customers who care most about that value, (5) the market category you frame "
        "yourself in so the value is obvious."
    ),
    "hormozi_value_equation": (
        "Perceived value = (Dream Outcome x Perceived Likelihood of Achievement) / "
        "(Time Delay x Effort & Sacrifice). Increase numerator, shrink denominator. A 'grand slam "
        "offer' stacks bonuses, guarantees, scarcity and urgency until saying no feels stupid."
    ),
    "business_model_canvas": (
        "9 blocks: Customer Segments, Value Propositions, Channels, Customer Relationships, "
        "Revenue Streams, Key Resources, Key Activities, Key Partners, Cost Structure. "
        "Innovation = change the relationship between blocks, not just the product."
    ),
    "business_model_patterns": (
        "Recombine known patterns (Gassmann 55): Razor-and-Blade, Freemium, Subscription, "
        "Long Tail, Two-Sided Market, Franchising, Direct Selling / DTC, Lock-In, Pay-Per-Use, "
        "Add-On, Flat Rate, Membership/Club, Crowdsourcing, White Label, Guaranteed Availability, "
        "Ingredient Branding, Experience Selling, Layer Player, Orchestrator, Robin Hood (rich "
        "subsidize poor)."
    ),
    "blue_ocean_errc": (
        "Eliminate–Reduce–Raise–Create grid. Eliminate factors the industry takes for granted, "
        "Reduce ones over-served, Raise ones under-served, Create ones the industry never offered. "
        "Goal: value up, cost down, competition irrelevant."
    ),
    "growth_loops": (
        "Replace linear funnels with loops where output re-feeds input: viral loop (users invite "
        "users), content loop (usage creates indexable content that acquires users), paid loop "
        "(revenue funds ads that fund revenue), UGC loop. Pick the loop the model can actually sustain."
    ),
    "eeat_authority": (
        "Experience, Expertise, Authoritativeness, Trust. Referent brands over-signal all four: "
        "named founders with a track record, published point of view, third-party validation, "
        "visible customers, transparent operations."
    ),
    "brand_voice_system": (
        "Define: 3-5 voice attributes (e.g. 'blunt, warm, expert, never corporate'), a do/don't "
        "word list, sentence-length rhythm, humor level, and 3 sample rewrites of the same message "
        "at different temperatures."
    ),
}

# ---------------------------------------------------------------------------
# 3b. QUALITY BAR — the rubric every agent is held to on its refine pass.
#     "ocurrencia" (wit/inventiveness) and "elocuencia" (eloquence) are made
#     concrete here instead of left as vibes, so a second LLM pass can
#     actually grade a draft against it.
# ---------------------------------------------------------------------------

CLICHE_BLOCKLIST: list[str] = [
    "synergy", "leverage synergies", "world-class", "cutting-edge", "best-in-class",
    "unlock your potential", "take it to the next level", "game-changer", "disruptive innovation",
    "seamless experience", "robust solution", "innovative solution", "empower", "holistic approach",
    "think outside the box", "paradigm shift", "value-added", "one-stop shop", "customer-centric",
    "passionate team", "state-of-the-art", "revolutionize", "elevate your brand",
]

QUALITY_BAR = """QUALITY BAR — every output is graded against this before it ships:

1. SPECIFIC over generic. Every claim names a mechanism, a number, or a named
   precedent. "Improve customer engagement" is a failure; "cut the checkout
   from 5 steps to 2, the way Amazon's 1-Click did" is a pass.
2. NO CLICHÉS. Banned words/phrases (if you catch yourself writing one of
   these, rewrite the sentence): """ + ", ".join(f'"{w}"' for w in CLICHE_BLOCKLIST) + """
3. OCURRENCIA (wit / inventiveness). The recommendation should be the kind
   a sharp strategist would actually say in a room, not the first bland
   answer a search engine would give. Prefer the non-obvious angle that is
   still defensible over the safe, forgettable one. When a field asks for
   alternatives, make them genuinely different bets, not three phrasings of
   the same idea.
4. ELOCUENCIA (eloquence). Short, rhythmic sentences. Concrete imagery over
   abstraction. Say the hard thing plainly instead of hedging it in five
   qualifiers. A tagline or manifesto should read like something a real
   brand would actually publish — not a template with blanks filled in.
5. CAUSAL, NOT DECORATIVE reasoning. Every recommendation traces to why it
   works (a mechanism, a precedent, a number) — never asserted by mere
   confidence.
6. NAME YOUR SOURCES. When a recommendation borrows a pattern from the
   reference material (a framework or a brand's origin playbook), say which
   one and why it transfers to this business specifically — do not silently
   reuse the example's own product/tagline.
"""


def quality_bar() -> str:
    return QUALITY_BAR


# ---------------------------------------------------------------------------
# 3c. DIAGNOSIS CALIBRATION — what the 0-5 scorecard axes mean, and the moat
#     types a referent brand defends. Injected into DiagnosisAgent so scores
#     are comparable across businesses instead of vibes.
# ---------------------------------------------------------------------------

REFERENT_SCORECARD_RUBRIC: dict[str, dict[int, str]] = {
    "positioning": {
        0: "No stated position; describes itself by category noun only ('a bakery').",
        1: "Position = a generic adjective ('quality', 'affordable', 'trusted').",
        2: "Has a target customer but the value claim is shared by every competitor.",
        3: "A real differentiator exists but isn't framed as a category or point of view.",
        4: "Clear Dunford-style position; customers can repeat why it's different.",
        5: "Owns a named category or point of view the market uses; competitors react to it.",
    },
    "brand_identity": {
        0: "Name + logo only; no voice, no story, interchangeable.",
        1: "Visual identity exists but no verbal identity or personality.",
        2: "Consistent look; voice is 'professional' default with no edge.",
        3: "Recognisable voice and a story, applied unevenly.",
        4: "One clear archetype; voice, story, visuals reinforce each other everywhere.",
        5: "Identity is a cultural asset — people wear it / quote it / defend it.",
    },
    "offer": {
        0: "Sells a commodity unit at market price; no packaging of value.",
        1: "Some bundling but price is the main lever.",
        2: "Tiered pricing exists; no anchor, guarantee, or reason to buy now.",
        3: "A differentiated offer with one strong element (guarantee OR bonus OR speed).",
        4: "Value equation clearly tilted — dream outcome high, effort/time low, risk removed.",
        5: "Grand-slam offer; saying no feels irrational; competitors can't match the terms.",
    },
    "fomo_desire": {
        0: "Always available, always discountable; no reason to act now.",
        1: "Occasional promos with fake 'ending soon' urgency.",
        2: "Some social proof shown; no scarcity, ritual, or exclusivity.",
        3: "One real desire lever running (waitlist / drop / members perk).",
        4: "Multiple honest levers + a cadence customers organise around.",
        5: "Demand outruns supply by design; resale/waitlist markets advertise for free.",
    },
    "distribution": {
        0: "One channel, passive; customers must find it.",
        1: "Present on 2-3 channels, no compounding loop.",
        2: "Paid acquisition works but every sale starts from zero.",
        3: "One growth loop partially working (content/referral/UGC).",
        4: "A sustained loop where output re-feeds input; CAC trending down.",
        5: "Category-defining distribution advantage (owned audience, network effect, shelf).",
    },
    "authority": {
        0: "Anonymous; no named founder, no track record, no third-party proof.",
        1: "Basic testimonials; nothing verifiable.",
        2: "Named team + some reviews; no published point of view.",
        3: "Founder has a voice; press or partnerships starting.",
        4: "Recognised expertise — cited, invited, referenced by others in the space.",
        5: "The reference others benchmark against; owns the definitive content on the topic.",
    },
}

MOAT_TYPES: list[str] = [
    "brand (customers pay a premium for the name / refuse substitutes)",
    "network effects (each user makes the product more valuable to the next)",
    "switching costs / lock-in (leaving is expensive or painful)",
    "economies of scale (unit cost falls with volume faster than rivals)",
    "counter-positioning (incumbents can't copy without cannibalising themselves)",
    "cornered resource (exclusive access to talent, supply, IP, location, distribution)",
    "process power (an operating system rivals can't replicate quickly — see McDonald's, Toyota)",
]


def scorecard_rubric_digest() -> str:
    lines = []
    for axis, levels in REFERENT_SCORECARD_RUBRIC.items():
        lines.append(f"{axis}:")
        lines.extend(f"  {n} = {txt}" for n, txt in levels.items())
    return "\n".join(lines)


def moat_types_digest() -> str:
    return "\n".join(f"- {m}" for m in MOAT_TYPES)


# ---------------------------------------------------------------------------
# 3d. POSITIONING & CATEGORY-DESIGN TESTS — Etapa 1. Pass/fail gates so the
#     agent can't ship a mushy enemy, a POV nobody disagrees with, or a
#     "new category" the business can't actually lead.
# ---------------------------------------------------------------------------

ENEMY_TEST: list[str] = [
    "It's a BEHAVIOUR or BELIEF customers currently hold or tolerate — not a named competitor.",
    "Naming it makes some prospects feel seen ('yes, that's exactly the problem').",
    "It's specific enough to picture — not 'inefficiency' or 'the old way'.",
    "The brand's whole offer is a coherent answer to this one enemy.",
    "It's still true in 5 years — not a temporary market quirk.",
]

POV_TEST: dict[str, str] = {
    "polarising": "A reasonable person in the market could disagree with it. If everyone nods, it says nothing.",
    "defensible": "There's evidence, logic, or the founder's earned experience behind it — not just an opinion.",
    "actionable": "It tells the customer (and the company) what to do differently, not just what to think.",
    "ownable": "This brand is uniquely credible saying it — a competitor copying it would look like a follower.",
    "durable": "It won't be embarrassing or obvious in 3 years.",
}

CATEGORY_KING_TEST: dict[str, str] = {
    "can_be_number_one": "Within a realistic horizon, can THIS business be the clear #1 of the category it names? If not, frame within an existing category instead.",
    "market_feels_the_pain": "Do customers already feel the problem the category solves, or must they be taught to feel it first (expensive, slow)?",
    "frame_is_teachable": "Can the category be explained in one sentence a customer repeats correctly?",
    "economics_concentrate": "Category kings take ~70%+ of category economics — is this category worth owning, or too small / too fragmented?",
    "not_just_a_feature": "Is this a category or a product feature dressed up as one?",
}

REFRAME_PATTERN = (
    "State the shift as FROM → TO: the frame customers use today (from) vs the "
    "frame this positioning installs (to). E.g. Dollar Shave Club: FROM 'razors "
    "are a grooming purchase you overpay for at the pharmacy' TO 'razors are a "
    "cheap consumable that should just show up'."
)


NAMING_CRITERIA: dict[str, str] = {
    "distinctive": "Doesn't blend into the category's naming conventions; a customer can pick it out of a list.",
    "memorable": "Sticks after one exposure — short, concrete, or surprising.",
    "sayable": "Survives being said out loud on a phone call and spelled without help.",
    "meaning_carrying": "Points at the positioning or the feeling, not a random word.",
    "room_to_grow": "Won't box the brand in if the product line expands.",
    "legally_plausible": "Not an obvious trademark/domain collision (flag for a real check, don't rule).",
}

STORY_SPINE_BEATS: list[str] = [
    "World: how things were / how the customer's world works by default.",
    "Problem: the specific friction or injustice in that world (this is the enemy).",
    "Insight: what the founder saw that others missed — the unlock.",
    "Mission: what the brand is now on a mission to make true for the customer.",
]

IDENTITY_NON_NEGOTIABLES_HINT = (
    "5 rules that must hold on every asset forever, phrased as checks a "
    "non-designer can apply: e.g. 'the enemy is named or implied in the first "
    "line', 'never discount the hero product', 'no stock photography of people "
    "in suits shaking hands'."
)


def naming_criteria_digest() -> str:
    return "\n".join(f"- {k}: {v}" for k, v in NAMING_CRITERIA.items())


# ---------------------------------------------------------------------------
# 3e. BUSINESS-MODEL & PRICING CALIBRATION — Etapa 3.
# ---------------------------------------------------------------------------

BUSINESS_MODEL_PATTERN_AXES: dict[str, str] = {
    "positioning_fit": "Does this pattern let the brand deliver its point of view, or fight it?",
    "margin_impact": "Effect on gross / contribution margin (+ / 0 / -).",
    "retention_impact": "Does it create a reason to stay (recurring value, lock-in, community)?",
    "execution_difficulty": "New capabilities, systems, or partners required (low / med / high).",
    "time_to_cash": "How fast it changes revenue (weeks / quarters / a year+).",
}

PRICING_PSYCH_TACTICS: list[str] = [
    "anchoring (show the expensive option first so the target tier feels reasonable)",
    "decoy / asymmetric dominance (a third option that makes the target tier obviously best)",
    "charm pricing ($X9 / $X7) — only where the brand isn't premium; round pricing signals confidence",
    "tiering by outcome not features (name tiers for who the customer wants to be)",
    "annual prepay discount (pull cash forward, cut churn — frame as 2 months free)",
    "good-better-best with the middle tier engineered to win",
    "unbundling the price anchor (charge for the thing competitors give away, give away what they charge for)",
    "usage-aligned pricing (price scales with the value the customer receives)",
    "founding-member / grandfather pricing that genuinely never returns",
]

UNIT_ECONOMICS_TARGETS_HINT = (
    "State target gross margin %, CAC ceiling, CAC payback (months), LTV:CAC ratio, "
    "and contribution margin — each with the ONE assumption it rests on. Use rough "
    "numbers from the profile where given; label the rest as assumptions to validate."
)


def bm_pattern_axes_digest() -> str:
    return "\n".join(f"- {k}: {v}" for k, v in BUSINESS_MODEL_PATTERN_AXES.items())


def pricing_tactics_digest() -> str:
    return "\n".join(f"- {t}" for t in PRICING_PSYCH_TACTICS)


def story_spine_digest() -> str:
    return "\n".join(f"{i+1}. {b}" for i, b in enumerate(STORY_SPINE_BEATS))


def positioning_tests_digest() -> str:
    return (
        "ENEMY TEST (all must pass):\n"
        + "\n".join(f"  - {x}" for x in ENEMY_TEST)
        + "\n\nPOV TEST (score each 0-2):\n"
        + "\n".join(f"  - {k}: {v}" for k, v in POV_TEST.items())
        + "\n\nCATEGORY-KING TEST (answer each before recommending 'design a new category'):\n"
        + "\n".join(f"  - {k}: {v}" for k, v in CATEGORY_KING_TEST.items())
        + f"\n\nREFRAME: {REFRAME_PATTERN}"
    )


# ---------------------------------------------------------------------------
# 4. TRANSFORMATION STAGES  (the staged program the orchestrator runs)
# ---------------------------------------------------------------------------

TRANSFORMATION_STAGES: list[dict] = [
    {
        "key": "diagnosis",
        "order": 0,
        "name": "Etapa 0 — Discovery & Diagnóstico",
        "goal": "Medir por qué el negocio es mediocre hoy: commoditización, propuesta de valor "
        "difusa, ausencia de categoría, unit economics, señales de autoridad.",
        "agent": "DiagnosisAgent",
        "deliverable": "Diagnóstico + 'Referent Potential Score' (0-100) + 3 palancas de mayor apalancamiento.",
    },
    {
        "key": "positioning",
        "order": 1,
        "name": "Etapa 1 — Posicionamiento & Diseño de Categoría",
        "goal": "Elegir alternativa competitiva, atributo único, valor, cliente que más lo valora "
        "y categoría-marco. Definir punto de vista y enemigo.",
        "agent": "PositioningAgent",
        "deliverable": "Statement de posicionamiento (Dunford), nombre de categoría, POV manifesto, enemigo.",
    },
    {
        "key": "brand_identity",
        "order": 2,
        "name": "Etapa 2 — Identidad de Marca & Narrativa",
        "goal": "Arquetipo primario, nombre (si aplica rebrand), tagline, manifiesto, sistema de "
        "voz, brief visual, arquitectura de marca.",
        "agent": "BrandIdentityAgent",
        "deliverable": "Brand book v1: arquetipo, tagline, manifiesto, voz (do/don't), brief visual.",
    },
    {
        "key": "business_model",
        "order": 3,
        "name": "Etapa 3 — Innovación de Modelo de Negocio & Oferta",
        "goal": "Rediseñar el canvas: nuevos revenue streams, patrón de modelo, oferta irresistible "
        "(Hormozi), pricing psicológico.",
        "agent": "BusinessModelAgent",
        "deliverable": "Canvas nuevo, 2-3 patrones aplicados, grand-slam offer, arquitectura de pricing.",
    },
    {
        "key": "fomo_engine",
        "order": 4,
        "name": "Etapa 4 — Motor de FOMO & Deseo",
        "goal": "Diseñar palancas de escasez, prueba social, exclusividad, ritual y urgencia "
        "adecuadas al negocio, sin romper la confianza.",
        "agent": "FOMOEngineAgent",
        "deliverable": "Playbook de 4-6 mecanismos con implementación concreta y guardarraíles anti-fake.",
    },
    {
        "key": "gtm",
        "order": 5,
        "name": "Etapa 5 — Go-to-Market & Growth Loops",
        "goal": "Canales, secuencia de lanzamiento (lightning strike), loop de crecimiento "
        "sostenible, funnel de ventas, contenido.",
        "agent": "GoToMarketAgent",
        "deliverable": "Plan GTM 90 días, 1 growth loop principal, guion de lanzamiento, mapa de canales.",
    },
    {
        "key": "restructuring",
        "order": 6,
        "name": "Etapa 6 — Reestructuración Empresarial & Operación",
        "goal": "Qué matar / mantener / escalar. Org, procesos, foco, unit economics, sistema "
        "operativo para sostener la nueva promesa.",
        "agent": "RestructuringAgent",
        "deliverable": "Kill/keep/scale list, rediseño org ligero, 3 procesos núcleo, KPIs de la promesa.",
    },
    {
        "key": "roadmap",
        "order": 7,
        "name": "Etapa 7 — Roadmap & Ritual de Ejecución",
        "goal": "Consolidar todas las etapas en un roadmap 90/180/365 con responsables, métricas "
        "y ritual de revisión.",
        "agent": "TransformationOrchestrator",
        "deliverable": "Roadmap 90/180/365, tablero de métricas, cadencia de revisión semanal/mensual.",
    },
]

STAGE_BY_KEY = {s["key"]: s for s in TRANSFORMATION_STAGES}
STAGE_ORDER = [s["key"] for s in TRANSFORMATION_STAGES]


def levers_digest() -> str:
    """Compact text block of every FOMO lever for prompt injection."""
    out = []
    for name, d in FOMO_LEVERS.items():
        out.append(
            f"- {name}: {d['mechanism']} Cases: {', '.join(d['cases'][:4])}. "
            f"Anti-pattern: {d['failure_mode']}"
        )
    return "\n".join(out)


def origins_digest() -> str:
    """Compact text block of every origin playbook for prompt injection."""
    out = []
    for name, d in BRAND_ORIGIN_PLAYBOOKS.items():
        out.append(
            f"- {name} (sells '{d['surface_product']}'): {d['real_engine']} "
            f"Levers: {', '.join(d['levers'])}. Lesson: {d['lesson']}"
        )
    return "\n".join(out)


def frameworks_digest(keys: list[str] | None = None) -> str:
    keys = keys or list(FRAMEWORKS.keys())
    return "\n".join(f"- {k}: {FRAMEWORKS[k]}" for k in keys if k in FRAMEWORKS)
