public class IncorrectConditionalOperator2 {
    public static void main(String[] args) {
        boolean isAdmin = false;
        int role = 1;
        if (isAdmin = role == 1) {
            System.out.println("Access granted");
        } else {
            System.out.println("Access denied");
        }
    }
}
