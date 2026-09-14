package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix014 {
    static int collatzSteps(int n) {
        int steps = 0;
        while (n != 1) {
            int next = (n % 2 == 0) ? n / 2 : 3 * n + 1;
            steps++;
            n = next;
        }
        return steps;
    }
}
