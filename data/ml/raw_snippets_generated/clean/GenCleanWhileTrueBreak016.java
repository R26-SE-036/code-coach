public class GenCleanWhileTrueBreak016 {
    static int spin(int count) {
        int rounds = 0;
        while (true) {
            rounds++;
            if (rounds > count) {
                break;
            }
        }
        return rounds;
    }
}
