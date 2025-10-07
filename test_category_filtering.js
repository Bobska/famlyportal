// Test script to verify payee-category filtering
// This can be run in browser console to test the functionality

console.log('=== Testing Payee-Category Filtering ===');

// Test data from our database
const testPayees = [
    {name: 'Woolworths', categories: [{id: 1, name: 'Food'}]},
    {name: 'Amazon', categories: [{id: 4, name: 'Entertainment'}, {id: 2, name: 'Food & Groceries'}]},
    {name: 'BP', categories: [{id: 15, name: 'Transport'}]},
    {name: 'Kmart', categories: []}
];

// Test the filtering logic
function testCategoryFiltering() {
    console.log('\n1. Testing Woolworths (should show only Food):');
    const woolworthsPayee = testPayees.find(p => p.name === 'Woolworths');
    console.log('Woolworths categories:', woolworthsPayee.categories.map(c => c.name));
    
    console.log('\n2. Testing Amazon (should show Entertainment and Food & Groceries):');
    const amazonPayee = testPayees.find(p => p.name === 'Amazon');
    console.log('Amazon categories:', amazonPayee.categories.map(c => c.name));
    
    console.log('\n3. Testing BP (should show only Transport):');
    const bpPayee = testPayees.find(p => p.name === 'BP');
    console.log('BP categories:', bpPayee.categories.map(c => c.name));
    
    console.log('\n4. Testing Kmart (should show all categories):');
    const kmartPayee = testPayees.find(p => p.name === 'Kmart');
    console.log('Kmart categories:', kmartPayee.categories.map(c => c.name));
    console.log('(Should fallback to showing all available categories)');
}

// Run the test
testCategoryFiltering();

console.log('\n=== Manual Testing Instructions ===');
console.log('1. Open the Add Transaction modal');
console.log('2. Select "Woolworths" as payee - category dropdown should only show "Food"');
console.log('3. Select "Amazon" as payee - category dropdown should only show "Entertainment" and "Food & Groceries"');
console.log('4. Select "BP" as payee - category dropdown should only show "Transport"');
console.log('5. Select a payee with no categories - category dropdown should show all available categories');