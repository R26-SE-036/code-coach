public class GenCleanFallThrough023 {
    static void printAll1(int[] stocks) {
        for (int value : stocks) {
            System.out.println(value);
        }
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

    static String join2(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static boolean isEven3(int attempts) {
        return attempts % 2 == 0;
    }

    static String status4(int code) {
        String label;
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "expired";
                break;
            default:
                label = "shipped";
        }
        return label;
    }

    static int largest5(int[] marks) {
        int best = marks[0];
        for (int i = 1; i < marks.length; i++) {
            if (marks[i] > best) {
                best = marks[i];
            }
        }
        return best;
    }
}
