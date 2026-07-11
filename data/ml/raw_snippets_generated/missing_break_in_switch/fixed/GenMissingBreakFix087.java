public class GenMissingBreakFix087 {
    static void printAll1(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }

    static String describeStudent(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "new";
                break;
            case 3:
                label = "final";
                break;
            case 4:
                label = "closed";
                break;
            default:
                label = "archived";
        }
        return label;
    }
}
