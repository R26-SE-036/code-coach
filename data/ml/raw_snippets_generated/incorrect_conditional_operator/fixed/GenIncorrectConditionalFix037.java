public class GenIncorrectConditionalFix037 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "draft";
                break;
            default:
                label = "expired";
        }
        return label;
    }

    static String join2(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static boolean matches(boolean armed, boolean open) {
        if (armed == open) {
            return true;
        }
        return false;
    }

    static String join3(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static boolean isEven4(int count) {
        return count % 2 == 0;
    }

    static String status5(int code) {
        String label;
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "new";
        }
        return label;
    }
}
