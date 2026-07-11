public class GenCleanStackedLabels015 {
    static String describe1(int count) {
        if (count < 5) {
            return "low";
        } else if (count > 20) {
            return "high";
        }
        return "medium";
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "archived";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static void printAll3(int[] marks) {
        for (int value : marks) {
            System.out.println(value);
        }
    }

    static String bucket(int code) {
        String label;
        switch (code) {
            case 1:
            case 2:
                label = "final";
                break;
            default:
                label = "active";
        }
        return label;
    }

    static void printAll4(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }
}
