package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix029 {
    static int stepsUntilDone(int target) {
        boolean done = false;
        boolean finished = false;
        int steps = 0;
        while (!done) {
            steps++;
            if (steps == target) {
                finished = true;
                done = true;
            }
        }
        return steps;
    }
}
