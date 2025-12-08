// run frontend test scenario

// puppeteer-runner.js (top of file)
// ===========================
// available test scenarios
// ===========================
const scenarios = {
    tony: [
        { message: "Hello homie, I'm Tony", expectedResponseKeywords: ["hi", "hello", "hey"] },
        {
            message: "I'm planning a business trip soon and would love your help.",
            expectedResponseKeywords: ["business trip", "sure", "help", "details"]
        },
        {
            message: "Some of my preferences: I prefer 4-star hotels, aisle seats on flights, and I like Japanese food.",
            expectedResponseKeywords: ["preferences", "stored", "noted", "travel preference"]
        },
        {
            message: "Next month I'm heading to Tokyo for work.",
            expectedResponseKeywords: ["tokyo", "trip", "store", "preference", "memory"]
        },
        {
            message: "Can you find available flights to Tokyo in the 10 - 17 of January? Give me the available departing flights.",
            expectedResponseKeywords: ["search", "tokyo", "available flights"]
        },
        {
            message: "Great, please book the first flight you found.",
            expectedResponseKeywords: ["book", "flight", "confirmed"]
        },
        {
            message: "Now can you search for the returning flights from Tokyo back to my home on the 17th of January? Show me the available return flights.",
            expectedResponseKeywords: [
                "search",
                "return",
                "returning",
                "tokyo",
                "available",
                "flights"
            ]
        }, {
            message: "Great, please book the first return flight you found.",
            expectedResponseKeywords: [
                "book",
                "booking",
                "reserved",
                "confirmed",
                "return flight",
                "flight"
            ]
        },
        {
            message: "Also, find me a hotel near Shinjuku. I want to book it for a week starting from 10th of January. Give me available hotels.",
            expectedResponseKeywords: ["hotel", "shinjuku"]
        },
        {
            message: "Book the best option for me.",
            expectedResponseKeywords: ["book", "hotel", "reservation"]
        }, {
            message: "Give me the trip summary for flight and hotel reservation, and total costs for this trip.",
            expectedResponseKeywords: [
                "summary",
                "flight",
                "hotel",
                "reservation",
                "retrieve",
                "travel",
                "preferences"
            ]
        },
        {
            message: "Thanks! Please remember my itinerary. That's all for now!",
            expectedResponseKeywords: [
                "welcome",
                "anytime",
                "help",
                "assist",
                "have a great day",
                "saved"
            ]
        }

    ],
    bob: [
        { message: "ping", expectedResponseKeywords: ["pong"] }
    ]
};

// ===========================
// message sending routine
// ===========================
async function sendMessage(page, message) {
    // Count current assistant messages
    const prevCount = await page.$$eval('#chatBox .assistant-message', els => els.length);

    await page.focus('#messageInput');
    await page.$eval('#messageInput', el => el.value = '');
    await page.type('#messageInput', message);

    await page.evaluate(() => {
        const btn = [...document.querySelectorAll('button')]
            .find(b => b.textContent.trim() === 'Send');
        btn?.click();
    });

    // Wait until a NEW assistant message appears
    await page.waitForFunction(
        (oldCount) => {
            const list = document.querySelectorAll('#chatBox .assistant-message');
            return list.length > oldCount;
        },
        {},            // options
        prevCount       // argument passed into page context
    );

    const response = await page.$$eval(
        '#chatBox .assistant-message',
        (els, oldCount) => {
            const newMsg = els[els.length - 1];
            const p = newMsg.querySelector('p');
            return p ? p.textContent.trim() : "";
        },
        prevCount
    );

    return response;

}

// ===========================
// actual code
// ===========================
// read argument
const scenarioName = process.argv[2];

// fail fast if missing
if (!scenarioName) {
    console.error('Error: no scenario name provided.');
    console.error('Usage: node puppeteer-runner.js <scenario-name>');
    console.error('Available scenarios:', Object.keys(scenarios).join(', '));
    process.exit(2); // non-zero -> failure
}

// fail if not found
const scenario = scenarios[scenarioName];
if (!scenario) {
    console.error(`Error: scenario "${scenarioName}" not found.`);
    console.error('Available scenarios:', Object.keys(scenarios).join(', '));
    process.exit(3);
}

// optional: validate scenario shape
if (!Array.isArray(scenario) || scenario.some(s => typeof s.message !== 'string')) {
    console.error(`Error: scenario "${scenarioName}" is malformed.`);
    process.exit(4);
}

//  ========================

const puppeteer = require('puppeteer');


(async () => {
    const browser = await puppeteer.launch({
        headless: false,
        defaultViewport: null,   // auto viewport
        slowMo: 50,              // optional: watch actions
        devtools: false          // optional: open DevTools
    });

    const page = await browser.newPage();

    await page.goto('http://127.0.0.1:8001');


    // Register & Login 
    await page.focus('#authUser');
    await page.$eval('#authUser', el => el.value = '');
    await page.type('#authUser', 'tony');

    await page.focus('#authPass');
    await page.$eval('#authPass', el => el.value = '');
    await page.type('#authPass', 'tony');

    await new Promise(resolve => setTimeout(resolve, 2000));

    await page.evaluate(() => {
        const btn = [...document.querySelectorAll('button')]
            .find(b => b.textContent.trim() === 'Register');
        btn?.click();
    });

    await new Promise(resolve => setTimeout(resolve, 2000));

    await page.evaluate(() => {
        const btn = [...document.querySelectorAll('button')]
            .find(b => b.textContent.trim() === 'Login');
        btn?.click();
    });

    // --- Robust normalization & matching helpers ---
    function normalizeText(s) {
        if (!s) return "";
        let out = s.normalize('NFKC');
        out = out.replace(/\u00A0/g, ' ');       // Replace non-breaking spaces
        out = out.replace(/[^\p{L}\p{N}\s]/gu, ' '); // Remove punctuation
        out = out.replace(/\s+/g, ' ').trim();   // Collapse whitespace
        return out.toLowerCase();
    }

    function findMatchedKeyword(reply, expectedKeywords) {
        const normReply = normalizeText(reply);

        for (const kw of expectedKeywords) {
            const normKw = normalizeText(kw);
            if (!normKw) continue;

            if (normReply.includes(normKw)) {
                return kw; // return matched keyword
            }
        }
        return null;
    }

    let passedAll = true;


    // sendMessage implementation assumed present...
    for (const step of scenario) {
        console.log('← User:', step.message);

        const expected = step.expectedResponseKeywords || [];
        let matchedKeyword = null;
        let reply = "";
        let attempt = 0;

        // Retry sendMessage up to 3 times
        while (attempt < 3) {
            attempt++;

            reply = await sendMessage(page, step.message);
            console.log(`→ Assistant (attempt ${attempt}):`, reply);

            // No expected keywords -> automatically pass
            if (expected.length === 0) {
                matchedKeyword = "(no keywords required)";
                break;
            }

            // Check keyword match
            matchedKeyword = findMatchedKeyword(reply, expected);

            if (matchedKeyword) {
                console.log(`✓ Passed: reply contains keyword "${matchedKeyword}"`);
                break; // success
            } else {
                console.log(`✗ Attempt ${attempt} failed: reply missing any of [${expected.join(", ")}]`);

                if (attempt < 3) {
                    console.log("⟳ Retrying...");
                    await new Promise(r => setTimeout(r, 1000)); // optional wait
                }
            }
        }

        // After all attempts, if still no match → fail scenario
        if (!matchedKeyword || matchedKeyword === null) {
            console.log("⛔ All retry attempts failed. Stopping scenario.");
            passedAll = false;
            break;
        }
    }
    // Only print success if all steps passed
    if (passedAll) {
        console.log("🎊 All steps passed — scenario succeeded!");
    }


    // await browser.close();
})();
