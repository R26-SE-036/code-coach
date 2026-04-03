package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug014 {
    public void validate(boolean active, int value) {
        boolean check = false;
        if (active && (check = value > 0)) {
            System.out.println("Valid and active");
        }
    }
}
