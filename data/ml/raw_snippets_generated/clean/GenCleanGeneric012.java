public class GenCleanGeneric012 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "draft";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static boolean isEven3(int limit) {
        return limit % 2 == 0;
    }

    static String join4(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String join5(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int average6(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
