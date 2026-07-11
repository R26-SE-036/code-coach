public class GenWhileNoUpdateBug125 {
    static void printAll1(int[] scores) {
        for (int value : scores) {
            System.out.println(value);
        }
    }

    static int gather(int quota, int total) {
        int sum = 0;
        while (quota < total) {
            sum += quota;
        }
        return sum;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "expired";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static String join3(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
