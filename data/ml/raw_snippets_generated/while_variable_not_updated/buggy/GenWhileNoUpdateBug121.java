public class GenWhileNoUpdateBug121 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "active";
                break;
            default:
                label = "final";
        }
        return label;
    }

    static int gather(int steps, int count) {
        int sum = 0;
        while (steps < count) {
            sum += steps;
        }
        return sum;
    }

    static void printAll2(int[] sizes) {
        for (int value : sizes) {
            System.out.println(value);
        }
    }
}
