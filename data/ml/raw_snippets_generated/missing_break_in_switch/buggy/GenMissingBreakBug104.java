public class GenMissingBreakBug104 {
    static void printAll1(int[] values) {
        for (int value : values) {
            System.out.println(value);
        }
    }

    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "active";
                break;
            case 2:
                label = "archived";
                break;
            case 3:
                label = "shipped";
            case 4:
                label = "expired";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static int sum2(int[] ages) {
        int total = 0;
        for (int i = 0; i < ages.length; i++) {
            total += ages[i];
        }
        return total;
    }
}
