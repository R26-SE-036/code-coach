package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix009 {
    static int minutesToCool(double temperature) {
        int minutes = 0;
        while (temperature > 25.0) {
            minutes++;
            temperature -= 1.5;
        }
        return minutes;
    }
}
