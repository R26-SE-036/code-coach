package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug003 {
    static int sumTo(int n) {
        int total = 0;
        int i = 1;
        while (i <= n) {
            total += i;
        }
        return total;
    }
}
