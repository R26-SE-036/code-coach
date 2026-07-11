public class GenCleanGeneric027 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "shipped";
                break;
            case 2:
                label = "new";
                break;
            default:
                label = "archived";
        }
        return label;
    }

    static int clamp3(int value, int low, int high) {
        if (value < low) {
            return low;
        } else if (value > high) {
            return high;
        }
        return value;
    }
}
