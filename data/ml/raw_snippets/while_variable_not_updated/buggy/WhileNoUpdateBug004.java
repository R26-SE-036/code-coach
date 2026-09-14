package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug004 {
    static int monthsToSave(double goal, double monthly) {
        double saved = 0;
        int months = 0;
        while (saved < goal) {
            months++;
        }
        return months;
    }
}
