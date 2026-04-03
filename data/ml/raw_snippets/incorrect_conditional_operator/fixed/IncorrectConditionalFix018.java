package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix018 {
    public void checkPermission(String user) {
        boolean allowed = user.equals("root");
        if (allowed) {
            System.out.println("Root access granted");
        }
    }
}
