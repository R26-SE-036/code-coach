package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug009 {
    static int minutesToCool(double temperature) {
        int minutes = 0;
        while (temperature > 25.0) {
            minutes++;
        }
        return minutes;
    }
}
