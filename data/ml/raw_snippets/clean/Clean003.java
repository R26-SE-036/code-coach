
public class Clean003 {
    public static void main(String[] args) {
        String role = "ADMIN";
        boolean hasAccess = role.equals("ADMIN");

        if (hasAccess) {
            System.out.println("Allowed");
        }
    }
}