public class GenMissingBreakBug061 {
    static String describeTask(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "paid";
            case 3:
                label = "shipped";
                break;
            default:
                label = "queued";
        }
        return label;
    }

    static void printAll1(int[] prices) {
        for (int value : prices) {
            System.out.println(value);
        }
    }
}
