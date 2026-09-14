package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug005 {
    static int halvings(int value) {
        int steps = 0;
        while (value > 1) {
            steps++;
        }
        return steps;
    }
}
