package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix030 {
    public void checkMatch(String a, String b) {
        boolean matched = a.equalsIgnoreCase(b);
        if (matched) {
            System.out.println("Strings match");
        }
    }
}
