package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug016 {
    public void checkTemperature(double temp) {
        boolean hot = false;
        if (hot = temp > 37.5) {
            System.out.println("Fever detected");
        }
    }
}
