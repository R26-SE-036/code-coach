package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug024 {
    static int gcd(int a, int b) {
        while (b != 0) {
            int remainder = a % b;
            a = b;
        }
        return a;
    }
}
