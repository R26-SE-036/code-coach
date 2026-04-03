package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix016 {
    public void checkTemperature(double temp) {
        boolean hot = temp > 37.5;
        if (hot) {
            System.out.println("Fever detected");
        }
    }
}
