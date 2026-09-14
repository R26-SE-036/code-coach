package data.ml.raw_snippets.while_variable_not_updated.buggy;

public class WhileNoUpdateBug017 {
    static int meetingPoint(int left, int right) {
        int moves = 0;
        while (left < right) {
            moves += 2;
        }
        return moves;
    }
}
