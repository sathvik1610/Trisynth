// Tough Test: Recursion, Global Arrays, Hoisting, Logic

int memo[20];
const int N = 10;

void main() {
    // 1. Initialize Global Array via Loop
    init_memo(); // Forward reference
    
    // 2. Complex Expression (Constant Folding Test)
    // (10 * 10 + 44) / 12 = 144 / 12 = 12
    int x = (10 * 10 + 44) / 12; 
    print(x); 

    // 3. Hoisted Logic Call
    if (is_even(x)) {
        print(1111); // Should print
    } else {
        print(0000);
    }

    // 4. Recursive Fibonacci with Memoization
    // Function defined at bottom (Hoisting + Recursion)
    int res = fib(N);
    print(res); // fib(10) = 55
}

void init_memo() {
    int i = 0;
    while (i < 20) {
        memo[i] = 0;
        ++i;
    }
}

bool is_even(int n) {
    if (n % 2 == 0) {
        return true;
    }
    return false;
}

int fib(int n) {
    if (n <= 1) return n;
    
    // Check memo
    if (memo[n] != 0) {
        return memo[n];
    }
    
    // Compute
    int res = fib(n - 1) + fib(n - 2);
    
    // Store (Global Side Effect)
    memo[n] = res;
    
    return res;
}
