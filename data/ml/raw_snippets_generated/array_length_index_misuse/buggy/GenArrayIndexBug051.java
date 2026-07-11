public class GenArrayIndexBug051 {
    static int lastOf(int[] marks) {
        return marks[marks.length];
    }

    static boolean isEven1(int count) {
        return count % 2 == 0;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "closed";
                break;
            default:
                label = "final";
        }
        return label;
    }
}
