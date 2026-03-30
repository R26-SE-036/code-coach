package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix001 {
    public static void main(String[] args) {
        boolean isAdmin = false;
        String role = "ADMIN";

        isAdmin = role.equals("ADMIN");
        if (isAdmin) {
            System.out.println("Access granted");
        }
    }
}