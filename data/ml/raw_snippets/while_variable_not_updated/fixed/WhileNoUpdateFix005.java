package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix005 {
    static int halvings(int value) {
        int steps = 0;
        while (value > 1) {
            steps++;
            value = value / 2;
        }
        return steps;
    }
}
