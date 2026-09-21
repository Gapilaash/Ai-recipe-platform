"""
Local recipe database. Completely free - no external recipe API needed.
Each recipe lists normalized ingredient names (lowercase, singular-ish)
used for matching against the user's pantry/detected ingredients.
"""

RECIPES = [
    {
        "id": 1, "name": "Classic Scrambled Eggs", "cook_time": 10, "servings": 2,
        "tags": ["vegetarian", "breakfast", "quick"],
        "ingredients": ["egg", "butter", "milk", "salt", "pepper"],
        "instructions": [
            "Crack eggs into a bowl, add a splash of milk, salt and pepper. Whisk well.",
            "Melt butter in a nonstick pan over medium-low heat.",
            "Pour in eggs, let sit 20 seconds, then gently push from edges to center.",
            "Keep folding gently until just set but still glossy. Remove from heat immediately.",
            "Serve right away."
        ]
    },
    {
        "id": 2, "name": "Garlic Butter Pasta", "cook_time": 20, "servings": 3,
        "tags": ["vegetarian", "dinner", "quick"],
        "ingredients": ["pasta", "garlic", "butter", "parmesan", "salt", "pepper", "olive oil"],
        "instructions": [
            "Boil pasta in salted water until al dente. Reserve 1 cup pasta water.",
            "In a large pan, melt butter with olive oil, add minced garlic, cook 1 min until fragrant.",
            "Add drained pasta to the pan with a splash of pasta water, toss well.",
            "Stir in parmesan, salt and pepper to taste. Add more pasta water if needed for a glossy sauce."
        ]
    },
    {
        "id": 3, "name": "Veggie Fried Rice", "cook_time": 20, "servings": 3,
        "tags": ["vegetarian", "dinner", "uses leftovers"],
        "ingredients": ["rice", "egg", "carrot", "onion", "soy sauce", "garlic", "green onion", "oil"],
        "instructions": [
            "Heat oil in a wok or large pan over high heat.",
            "Scramble the egg, remove and set aside.",
            "Add more oil, sauté onion, garlic and diced carrot until softened.",
            "Add cold cooked rice, breaking up clumps, stir-fry 3-4 minutes.",
            "Add soy sauce and scrambled egg back in, toss well.",
            "Top with sliced green onion."
        ]
    },
    {
        "id": 4, "name": "Tomato Basil Soup", "cook_time": 30, "servings": 4,
        "tags": ["vegetarian", "dinner", "soup"],
        "ingredients": ["tomato", "onion", "garlic", "vegetable broth", "basil", "butter", "cream", "salt"],
        "instructions": [
            "Sauté onion and garlic in butter until soft.",
            "Add chopped tomatoes and broth, simmer 15-20 minutes.",
            "Blend until smooth (use a blender or immersion blender).",
            "Stir in cream and torn basil leaves, season with salt.",
            "Simmer 5 more minutes and serve."
        ]
    },
    {
        "id": 5, "name": "Chicken Stir Fry", "cook_time": 25, "servings": 3,
        "tags": ["dinner", "high-protein"],
        "ingredients": ["chicken breast", "broccoli", "carrot", "soy sauce", "garlic", "ginger", "oil"],
        "instructions": [
            "Cut chicken into bite-size pieces, season lightly.",
            "Heat oil in a wok, stir-fry chicken until cooked through, remove.",
            "Add broccoli and carrot, stir-fry 3-4 minutes until crisp-tender.",
            "Add garlic and ginger, cook 30 seconds until fragrant.",
            "Return chicken to the pan, add soy sauce, toss and cook 2 more minutes."
        ]
    },
    {
        "id": 6, "name": "Simple Omelette", "cook_time": 10, "servings": 1,
        "tags": ["vegetarian", "breakfast", "quick"],
        "ingredients": ["egg", "cheese", "butter", "salt", "pepper"],
        "instructions": [
            "Whisk eggs with salt and pepper.",
            "Melt butter in a small nonstick pan over medium heat.",
            "Pour in eggs, let set slightly, sprinkle cheese on one half.",
            "Fold in half once mostly set and cheese starts melting, slide onto plate."
        ]
    },
    {
        "id": 7, "name": "Grilled Cheese Sandwich", "cook_time": 10, "servings": 1,
        "tags": ["vegetarian", "quick", "lunch"],
        "ingredients": ["bread", "cheese", "butter"],
        "instructions": [
            "Butter one side of each bread slice.",
            "Place cheese between the slices, butter-side out.",
            "Grill in a pan over medium heat 3-4 minutes per side until golden and cheese melts."
        ]
    },
    {
        "id": 8, "name": "Classic Guacamole", "cook_time": 10, "servings": 4,
        "tags": ["vegetarian", "vegan", "no-cook"],
        "ingredients": ["avocado", "lime", "onion", "tomato", "cilantro", "salt"],
        "instructions": [
            "Mash avocados in a bowl.",
            "Finely dice onion, tomato and cilantro, mix in.",
            "Add lime juice and salt, stir well and adjust seasoning."
        ]
    },
    {
        "id": 9, "name": "Beef Tacos", "cook_time": 25, "servings": 4,
        "tags": ["dinner", "high-protein"],
        "ingredients": ["ground beef", "onion", "garlic", "tortilla", "cheese", "tomato", "lettuce", "salt", "pepper"],
        "instructions": [
            "Brown ground beef with diced onion and garlic, season with salt and pepper.",
            "Warm tortillas in a dry pan.",
            "Fill tortillas with beef, top with cheese, diced tomato and shredded lettuce."
        ]
    },
    {
        "id": 10, "name": "Pancakes", "cook_time": 20, "servings": 4,
        "tags": ["vegetarian", "breakfast"],
        "ingredients": ["flour", "egg", "milk", "sugar", "butter", "baking powder", "salt"],
        "instructions": [
            "Mix flour, sugar, baking powder and salt in a bowl.",
            "Whisk in milk, egg and melted butter until just combined (small lumps ok).",
            "Pour batter onto a hot greased griddle, cook until bubbles form, flip.",
            "Cook other side until golden. Serve with syrup or fruit."
        ]
    },
    {
        "id": 11, "name": "Lentil Soup", "cook_time": 40, "servings": 4,
        "tags": ["vegetarian", "vegan", "dinner", "soup"],
        "ingredients": ["lentils", "onion", "carrot", "celery", "garlic", "vegetable broth", "cumin", "salt"],
        "instructions": [
            "Sauté onion, carrot, celery and garlic until softened.",
            "Add lentils, broth and cumin, bring to a boil.",
            "Reduce heat, simmer 25-30 minutes until lentils are tender.",
            "Season with salt, blend partially if a thicker texture is desired."
        ]
    },
    {
        "id": 12, "name": "Caprese Salad", "cook_time": 10, "servings": 2,
        "tags": ["vegetarian", "no-cook", "salad"],
        "ingredients": ["tomato", "mozzarella", "basil", "olive oil", "salt", "pepper"],
        "instructions": [
            "Slice tomatoes and mozzarella into rounds.",
            "Arrange alternating on a plate with basil leaves.",
            "Drizzle with olive oil, season with salt and pepper."
        ]
    },
    {
        "id": 13, "name": "Baked Salmon", "cook_time": 25, "servings": 2,
        "tags": ["high-protein", "dinner"],
        "ingredients": ["salmon", "lemon", "garlic", "olive oil", "salt", "pepper"],
        "instructions": [
            "Preheat oven to 400°F (200°C).",
            "Place salmon on a lined tray, drizzle with olive oil, minced garlic, salt and pepper.",
            "Top with lemon slices.",
            "Bake 12-15 minutes until it flakes easily with a fork."
        ]
    },
    {
        "id": 14, "name": "Vegetable Curry", "cook_time": 35, "servings": 4,
        "tags": ["vegetarian", "vegan", "dinner"],
        "ingredients": ["potato", "carrot", "onion", "garlic", "ginger", "coconut milk", "curry powder", "tomato", "salt"],
        "instructions": [
            "Sauté onion, garlic and ginger until fragrant.",
            "Add curry powder, cook 30 seconds.",
            "Add potato, carrot and tomato, stir to coat.",
            "Pour in coconut milk, simmer 20-25 minutes until vegetables are tender.",
            "Season with salt to taste."
        ]
    },
    {
        "id": 15, "name": "Banana Pancake Smoothie Bowl", "cook_time": 10, "servings": 1,
        "tags": ["vegetarian", "breakfast", "no-cook"],
        "ingredients": ["banana", "milk", "yogurt", "honey", "oats"],
        "instructions": [
            "Blend banana, milk, yogurt and honey until smooth.",
            "Pour into a bowl and top with oats and extra banana slices."
        ]
    },
    {
        "id": 16, "name": "Chicken Noodle Soup", "cook_time": 40, "servings": 4,
        "tags": ["dinner", "soup"],
        "ingredients": ["chicken breast", "carrot", "celery", "onion", "garlic", "chicken broth", "pasta", "salt", "pepper"],
        "instructions": [
            "Sauté onion, carrot, celery and garlic in a pot until softened.",
            "Add broth and chicken, simmer 15-20 minutes until chicken is cooked.",
            "Remove chicken, shred it, return to pot.",
            "Add noodles, cook until tender. Season with salt and pepper."
        ]
    },
    {
        "id": 17, "name": "Avocado Toast", "cook_time": 10, "servings": 1,
        "tags": ["vegetarian", "breakfast", "quick"],
        "ingredients": ["bread", "avocado", "lemon", "salt", "pepper", "olive oil"],
        "instructions": [
            "Toast the bread.",
            "Mash avocado with lemon juice, salt and pepper.",
            "Spread onto toast, drizzle with olive oil."
        ]
    },
    {
        "id": 18, "name": "Beef and Broccoli", "cook_time": 25, "servings": 3,
        "tags": ["dinner", "high-protein"],
        "ingredients": ["beef", "broccoli", "garlic", "soy sauce", "ginger", "oil", "sugar"],
        "instructions": [
            "Slice beef thinly against the grain.",
            "Stir-fry beef in hot oil until browned, remove.",
            "Stir-fry broccoli, garlic and ginger 2-3 minutes.",
            "Return beef to pan, add soy sauce and a pinch of sugar, toss and cook 2 minutes."
        ]
    },
    {
        "id": 19, "name": "Margherita Pizza", "cook_time": 30, "servings": 2,
        "tags": ["vegetarian", "dinner"],
        "ingredients": ["pizza dough", "tomato sauce", "mozzarella", "basil", "olive oil", "salt"],
        "instructions": [
            "Preheat oven as hot as it goes (ideally 475°F/245°C).",
            "Roll out dough, spread tomato sauce leaving a border.",
            "Top with torn mozzarella.",
            "Bake 10-12 minutes until crust is golden.",
            "Top with fresh basil and a drizzle of olive oil."
        ]
    },
    {
        "id": 20, "name": "Greek Salad", "cook_time": 15, "servings": 3,
        "tags": ["vegetarian", "no-cook", "salad"],
        "ingredients": ["cucumber", "tomato", "onion", "feta", "olive", "olive oil", "lemon", "salt"],
        "instructions": [
            "Chop cucumber, tomato and onion into chunks.",
            "Combine in a bowl with olives and cubed feta.",
            "Dress with olive oil, lemon juice and salt, toss gently."
        ]
    },
    {
        "id": 21, "name": "Shrimp Scampi", "cook_time": 20, "servings": 3,
        "tags": ["dinner", "high-protein"],
        "ingredients": ["shrimp", "pasta", "garlic", "butter", "lemon", "olive oil", "salt", "pepper"],
        "instructions": [
            "Cook pasta in salted water until al dente.",
            "Sauté garlic in butter and olive oil until fragrant.",
            "Add shrimp, cook until pink, about 2-3 minutes per side.",
            "Toss with pasta, lemon juice, salt and pepper."
        ]
    },
    {
        "id": 22, "name": "Black Bean Quesadillas", "cook_time": 15, "servings": 2,
        "tags": ["vegetarian", "quick"],
        "ingredients": ["tortilla", "black beans", "cheese", "onion", "salt"],
        "instructions": [
            "Mash black beans slightly, mix with diced onion and salt.",
            "Spread on half a tortilla, top with cheese, fold over.",
            "Cook in a dry pan 2-3 minutes per side until golden and cheese melts."
        ]
    },
    {
        "id": 23, "name": "Mushroom Risotto", "cook_time": 40, "servings": 3,
        "tags": ["vegetarian", "dinner"],
        "ingredients": ["rice", "mushroom", "onion", "garlic", "vegetable broth", "parmesan", "butter", "white wine"],
        "instructions": [
            "Sauté mushrooms until browned, set aside.",
            "Sauté onion and garlic in butter, add rice, toast 1 minute.",
            "Add wine, stir until absorbed.",
            "Add broth one ladle at a time, stirring until absorbed before adding more, about 20 min.",
            "Stir in mushrooms and parmesan before serving."
        ]
    },
    {
        "id": 24, "name": "Egg Fried Noodles", "cook_time": 15, "servings": 2,
        "tags": ["vegetarian", "quick"],
        "ingredients": ["noodles", "egg", "carrot", "green onion", "soy sauce", "garlic", "oil"],
        "instructions": [
            "Cook noodles according to package, drain.",
            "Scramble egg in hot oil, remove.",
            "Sauté garlic and carrot briefly, add noodles and soy sauce.",
            "Toss in egg and green onion, stir-fry 2 minutes."
        ]
    },
    {
        "id": 25, "name": "Classic Hummus", "cook_time": 10, "servings": 4,
        "tags": ["vegetarian", "vegan", "no-cook"],
        "ingredients": ["chickpeas", "garlic", "lemon", "tahini", "olive oil", "salt"],
        "instructions": [
            "Blend chickpeas, garlic, lemon juice and tahini until smooth.",
            "Add olive oil and salt, blend again, adding water for desired consistency."
        ]
    },
    {
        "id": 26, "name": "Baked Chicken Thighs", "cook_time": 40, "servings": 4,
        "tags": ["dinner", "high-protein"],
        "ingredients": ["chicken thighs", "garlic", "lemon", "olive oil", "salt", "pepper"],
        "instructions": [
            "Preheat oven to 425°F (220°C).",
            "Toss chicken thighs with olive oil, minced garlic, salt and pepper.",
            "Arrange on a tray, top with lemon slices.",
            "Bake 35-40 minutes until skin is crispy and cooked through."
        ]
    },
    {
        "id": 27, "name": "Vegetable Omelette", "cook_time": 15, "servings": 2,
        "tags": ["vegetarian", "breakfast"],
        "ingredients": ["egg", "onion", "tomato", "bell pepper", "cheese", "butter", "salt", "pepper"],
        "instructions": [
            "Whisk eggs with salt and pepper.",
            "Sauté diced onion, tomato and bell pepper in butter until soft.",
            "Pour eggs over vegetables, cook until mostly set.",
            "Sprinkle cheese, fold and serve."
        ]
    },
    {
        "id": 28, "name": "Peanut Butter Banana Oatmeal", "cook_time": 10, "servings": 1,
        "tags": ["vegetarian", "breakfast", "quick"],
        "ingredients": ["oats", "banana", "peanut butter", "milk", "honey"],
        "instructions": [
            "Cook oats with milk according to package directions.",
            "Stir in peanut butter and sliced banana.",
            "Drizzle with honey before serving."
        ]
    },
    {
        "id": 29, "name": "Stuffed Bell Peppers", "cook_time": 45, "servings": 4,
        "tags": ["dinner"],
        "ingredients": ["bell pepper", "ground beef", "rice", "onion", "tomato", "cheese", "garlic", "salt"],
        "instructions": [
            "Preheat oven to 375°F (190°C). Cut tops off peppers and remove seeds.",
            "Brown ground beef with onion and garlic, mix in cooked rice and chopped tomato.",
            "Season with salt, stuff into peppers.",
            "Top with cheese, bake 25-30 minutes until peppers are tender."
        ]
    },
    {
        "id": 30, "name": "Caesar Salad", "cook_time": 15, "servings": 2,
        "tags": ["no-cook", "salad"],
        "ingredients": ["lettuce", "parmesan", "bread", "garlic", "olive oil", "lemon", "egg"],
        "instructions": [
            "Toast cubed bread with olive oil and garlic to make croutons.",
            "Whisk egg yolk, lemon juice and olive oil for dressing.",
            "Toss lettuce with dressing, top with parmesan and croutons."
        ]
    },
    {
        "id": 31, "name": "Chili Con Carne", "cook_time": 45, "servings": 4,
        "tags": ["dinner", "high-protein"],
        "ingredients": ["ground beef", "kidney beans", "tomato", "onion", "garlic", "chili powder", "cumin", "salt"],
        "instructions": [
            "Brown ground beef with onion and garlic.",
            "Add chili powder and cumin, cook 1 minute.",
            "Add tomatoes and kidney beans, simmer 30 minutes.",
            "Season with salt to taste."
        ]
    },
    {
        "id": 32, "name": "Cucumber Yogurt Salad", "cook_time": 10, "servings": 2,
        "tags": ["vegetarian", "no-cook", "salad"],
        "ingredients": ["cucumber", "yogurt", "garlic", "lemon", "salt"],
        "instructions": [
            "Dice or grate cucumber, salt lightly and let sit 5 minutes, drain excess water.",
            "Mix with yogurt, minced garlic and lemon juice."
        ]
    },
    {
        "id": 33, "name": "French Toast", "cook_time": 15, "servings": 2,
        "tags": ["vegetarian", "breakfast"],
        "ingredients": ["bread", "egg", "milk", "sugar", "butter", "cinnamon"],
        "instructions": [
            "Whisk egg, milk, sugar and cinnamon in a shallow dish.",
            "Dip bread slices, coating both sides.",
            "Cook in buttered pan over medium heat until golden on both sides."
        ]
    },
    {
        "id": 34, "name": "Pesto Pasta", "cook_time": 20, "servings": 3,
        "tags": ["vegetarian", "quick", "dinner"],
        "ingredients": ["pasta", "basil", "parmesan", "garlic", "olive oil", "pine nuts", "salt"],
        "instructions": [
            "Cook pasta in salted water until al dente.",
            "Blend basil, parmesan, garlic, pine nuts and olive oil into a pesto.",
            "Toss pasta with pesto, adding pasta water as needed."
        ]
    },
    {
        "id": 35, "name": "Roasted Vegetable Medley", "cook_time": 35, "servings": 4,
        "tags": ["vegetarian", "vegan", "side"],
        "ingredients": ["potato", "carrot", "bell pepper", "onion", "olive oil", "salt", "pepper"],
        "instructions": [
            "Preheat oven to 425°F (220°C).",
            "Chop vegetables into even chunks, toss with olive oil, salt and pepper.",
            "Spread on a tray, roast 25-30 minutes, tossing halfway, until tender and browned."
        ]
    },
    {
        "id": 36, "name": "Tuna Salad Sandwich", "cook_time": 10, "servings": 2,
        "tags": ["quick", "lunch", "no-cook"],
        "ingredients": ["tuna", "mayonnaise", "celery", "onion", "bread", "salt", "pepper"],
        "instructions": [
            "Mix tuna with mayonnaise, diced celery and onion, salt and pepper.",
            "Spread onto bread slices."
        ]
    },
    {
        "id": 37, "name": "Butter Chicken", "cook_time": 45, "servings": 4,
        "tags": ["dinner", "high-protein"],
        "ingredients": ["chicken breast", "tomato", "onion", "garlic", "ginger", "cream", "butter", "curry powder", "salt"],
        "instructions": [
            "Sauté onion, garlic and ginger in butter until soft.",
            "Add curry powder, cook 1 minute, then add chopped tomato, simmer 10 minutes.",
            "Blend sauce until smooth, return to pan.",
            "Add chicken pieces, simmer 15-20 minutes until cooked through.",
            "Stir in cream, season with salt."
        ]
    },
    {
        "id": 38, "name": "Zucchini Noodles with Tomato Sauce", "cook_time": 20, "servings": 2,
        "tags": ["vegetarian", "vegan", "low-carb"],
        "ingredients": ["zucchini", "tomato", "garlic", "onion", "olive oil", "basil", "salt"],
        "instructions": [
            "Spiralize zucchini into noodles.",
            "Sauté onion and garlic in olive oil, add chopped tomatoes, simmer 10-15 minutes.",
            "Add zucchini noodles, toss 2-3 minutes until just softened.",
            "Season with salt and fresh basil."
        ]
    },
    {
        "id": 39, "name": "Egg Salad", "cook_time": 15, "servings": 2,
        "tags": ["vegetarian", "quick", "lunch"],
        "ingredients": ["egg", "mayonnaise", "mustard", "celery", "salt", "pepper", "bread"],
        "instructions": [
            "Hard boil eggs (about 10 minutes), cool, peel and chop.",
            "Mix with mayonnaise, mustard, diced celery, salt and pepper.",
            "Serve on bread or as-is."
        ]
    },
    {
        "id": 40, "name": "Baked Sweet Potato", "cook_time": 45, "servings": 2,
        "tags": ["vegetarian", "vegan", "side"],
        "ingredients": ["sweet potato", "olive oil", "salt", "butter"],
        "instructions": [
            "Preheat oven to 400°F (200°C).",
            "Pierce sweet potatoes with a fork, rub with olive oil and salt.",
            "Bake 40-45 minutes until tender.",
            "Split open, top with butter."
        ]
    },
    {
        "id": 41, "name": "Chicken Quesadillas", "cook_time": 20, "servings": 2,
        "tags": ["quick", "high-protein"],
        "ingredients": ["chicken breast", "tortilla", "cheese", "onion", "bell pepper", "salt"],
        "instructions": [
            "Cook diced chicken with onion and bell pepper, season with salt.",
            "Place filling and cheese on half a tortilla, fold over.",
            "Cook in a dry pan 2-3 minutes per side until golden and cheese melts."
        ]
    },
    {
        "id": 42, "name": "Overnight Oats", "cook_time": 5, "servings": 1,
        "tags": ["vegetarian", "breakfast", "no-cook", "make-ahead"],
        "ingredients": ["oats", "milk", "yogurt", "honey", "banana"],
        "instructions": [
            "Combine oats, milk, yogurt and honey in a jar.",
            "Top with sliced banana, cover and refrigerate overnight.",
            "Stir and eat cold in the morning."
        ]
    },
]

# Master ingredient list (used for suggestions / autocomplete in the UI)
ALL_INGREDIENTS = sorted(set(i for r in RECIPES for i in r["ingredients"]))
