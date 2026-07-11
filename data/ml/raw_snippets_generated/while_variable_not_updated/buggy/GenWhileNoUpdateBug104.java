public class GenWhileNoUpdateBug104 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "active";
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

    static void printAll3(int[] values) {
        for (int value : values) {
            System.out.println(value);
        }
    }

    static String join4(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static int gather(int limit, int quota) {
        int sum = 0;
        while (limit < quota) {
            sum += limit;
        }
        return sum;
    }
}
