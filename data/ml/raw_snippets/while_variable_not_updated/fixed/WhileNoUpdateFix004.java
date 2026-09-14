package data.ml.raw_snippets.while_variable_not_updated.fixed;

public class WhileNoUpdateFix004 {
    static int monthsToSave(double goal, double monthly) {
        double saved = 0;
        int months = 0;
        while (saved < goal) {
            months++;
            saved += monthly;
        }
        return months;
    }
}
