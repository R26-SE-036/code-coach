public class GenMissingBreakBug082 {
    static void printAll1(int[] values) {
        for (int value : values) {
            System.out.println(value);
        }
    }

    static String describeOrder(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "archived";
            case 2:
                label = "shipped";
                break;
            case 3:
                label = "closed";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "active";
        }
        return label;
    }
}
