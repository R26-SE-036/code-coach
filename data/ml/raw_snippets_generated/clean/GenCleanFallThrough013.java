public class GenCleanFallThrough013 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void printPermissions(int level) {
        switch (level) {
            case 3:
                System.out.println("can delete");
                // fall through: higher levels include lower rights
            case 2:
                System.out.println("can edit");
                // fall through
            case 1:
                System.out.println("can view");
                break;
            default:
                System.out.println("no access");
        }
    }
}
