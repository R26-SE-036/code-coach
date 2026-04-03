package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix014 {
    public void validate(boolean active, int value) {
        boolean check = value > 0;
        if (active && check) {
            System.out.println("Valid and active");
        }
    }
}
