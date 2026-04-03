package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug015 {
    public String classify(int score) {
        boolean pass = false;
        return (pass = score >= 50) ? "Pass" : "Fail";
    }
}
